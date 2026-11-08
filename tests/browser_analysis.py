"""Browser checks for the separate, read-only course-analysis demonstration."""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:5000')
    parser.add_argument('--output', type=Path, default=Path('docs/screenshots/analysis'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    checks = []

    def passed(name):
        checks.append({'check': name, 'passed': True})
        print('PASS', name, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1024}, reduced_motion='reduce')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            page.goto(args.base_url + '/analysis')
            expect(page.get_by_role('heading', name='Project analysis', exact=True)).to_be_visible()
            expect(page.locator('.metrics')).to_contain_text('264')
            expect(page.locator('.metrics')).to_contain_text('63.6%')
            expect(page.locator('.metrics')).to_contain_text('0.595')
            for figure in page.locator('figure img').all():
                figure.scroll_into_view_if_needed()
                expect(figure).to_be_visible()
                expect(figure).to_have_js_property('complete', True)
                assert figure.evaluate('(image) => image.naturalWidth > 0')
            expect(page.locator('figure')).to_have_count(5)
            expect(page.locator('figure a')).to_have_count(5)
            page.screenshot(path=str(args.output / 'desktop-analysis.png'), full_page=True)
            passed('Analysis shows measured metrics, cleaning results, comparison, limitations and five loaded figures')

            page.set_viewport_size({'width': 390, 'height': 844})
            page.goto(args.base_url + '/analysis')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(args.output / 'mobile-analysis.png'), full_page=True)

            def predict(question):
                page.locator('#classify-question').fill(question)
                page.get_by_role('button', name='Predict FAQ topic').click()
                expect(page.get_by_role('button', name='Predict FAQ topic')).to_be_enabled()

            predict('Who teaches BSCS?')
            expect(page.locator('#classify-results li').first).to_contain_text('FAQ-018')
            expect(page.locator('#classify-status')).to_contain_text('uncalibrated')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            passed('Mobile analysis fits viewport and classifier predicts using the trained local model')

            predict('zzzzxyyqqvv')
            expect(page.locator('#classify-status')).to_contain_text('No known vocabulary')
            expect(page.locator('#classify-results li')).to_have_count(0)
            passed('Completely unseen vocabulary produces an honest no-evidence state')

            predict('Show my student grades')
            expect(page.locator('#classify-status')).to_contain_text('private student records')
            expect(page.locator('#classify-results li')).to_have_count(0)
            passed('Private-record requests are rejected without predictions')

            page.route('**/api/classify', lambda route: route.fulfill(status=503, content_type='application/json',
                        body=json.dumps({'success': False, 'error': 'Model unavailable; restart after training.'})))
            predict('Who teaches BSCS?')
            expect(page.locator('#classify-status')).to_contain_text('Model unavailable')
            page.unroute_all(behavior='wait')
            predict('Who teaches BSCS?')
            expect(page.locator('#classify-results li').first).to_contain_text('FAQ-018')
            passed('Simulated model failure is readable and a later real prediction recovers')

            attack = '<img src=x onerror="window.ccitInjected=1">'
            page.route('**/api/classify', lambda route: route.fulfill(status=200, content_type='application/json',
                        body=json.dumps({'success': True, 'predictions': [{'faq_id': 'TEST', 'title': attack, 'score': .5}], 'note': 'Synthetic safety fixture'})))
            predict(attack)
            expect(page.locator('#classify-results strong')).to_have_text(attack)
            assert page.locator('#classify-results img').count() == 0
            assert page.evaluate('window.ccitInjected === undefined')
            page.get_by_role('link', name='Back to chat').click()
            expect(page.locator('#welcome')).to_be_visible()
            passed('Prediction text remains safe and Back to chat returns to the original UI')
            assert not errors, errors
        finally:
            browser.close()
    (args.output / 'browser-results.json').write_text(json.dumps({
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'Local trained classifier; simulated failure/safety fixture; no AI API calls', 'checks': checks,
    }, indent=2) + '\n', encoding='utf-8')
    print(f'{len(checks)} analysis browser scenarios passed')


if __name__ == '__main__':
    main()
