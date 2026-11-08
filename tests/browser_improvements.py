"""Browser regression checks for focused answers, context and explicit recovery.

Run against a FAQ-mode server. Provider failures below are deliberately simulated;
all successful source answers come from the actual running Flask application.
"""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:5000')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--output', type=Path, default=Path('docs/screenshots/improvements'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []

    def passed(name):
        results.append({'check': name, 'passed': True})
        print('PASS', name, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium, headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce',
                                      permissions=['clipboard-read', 'clipboard-write'])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            health = context.request.get(args.base_url + '/api/health').json()
            assert health['mode'] == 'faq' and health['ready'], 'Run the server in labeled FAQ mode first'

            def home():
                page.unroute_all(behavior='wait')
                page.goto(args.base_url)
                expect(page.locator('.topic-card').first).to_be_enabled()

            def ask(question):
                page.locator('#question').fill(question)
                page.locator('#question').press('Enter')
                expect(page.locator('.typing')).to_have_count(0)
                expect(page.locator('#clear')).to_be_enabled()

            home()
            ask('Do you guys offer BSCS?')
            reply = page.locator('.message.assistant').last
            expect(reply.locator('.message-text')).to_contain_text('Yes.')
            assert len(reply.locator('.message-text').inner_text()) < 180
            expect(reply.locator('.message-text strong')).to_have_text('Bachelor of Science in Computer Science (BSCS)')
            expect(reply.locator('.message-sources, .source-warning, .source-details, .source-provenance')).to_have_count(0)
            assert not any(value in reply.inner_text() for value in ['FAQ-006', 'Source:', 'unconfirmed', 'Checked against', 'supplied document'])
            assert reply.locator('strong').evaluate('(element) => getComputedStyle(element).fontWeight') == '600'
            page.screenshot(path=str(args.output / 'mobile-focused-answer.png'), full_page=True)
            reply.locator('.copy-answer').click()
            expect(reply.locator('.copy-answer')).to_have_text('Copied')
            copied = page.evaluate('navigator.clipboard.readText()')
            assert 'Bachelor of Science in Computer Science' in copied and '**' not in copied
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            passed('Direct answer, bold key fact, no source/verification clutter, and plain-text copy')

            home()
            ask('What is BSCS?')
            ask('What jobs can I get after this program?')
            reply = page.locator('.message.assistant').last
            expect(reply.locator('.message-text strong').filter(has_text='Machine Learning Engineer')).to_have_count(1)
            assert reply.locator('.message-text li').count() > 3
            page.screenshot(path=str(args.output / 'mobile-careers-followup.png'), full_page=True)
            page.locator('#clear').click()
            page.locator('#confirm-clear').click()
            ask('What jobs can I get after this program?')
            expect(page.locator('.message.assistant').last).to_contain_text('Which program do you mean')
            ask('BSIT')
            expect(page.locator('.message.assistant').last.locator('.message-text')).to_contain_text('Network Administrator')
            passed('Program follow-up, New chat context reset, and clarification completion')

            home()
            requests = []

            def transient(route):
                requests.append(route.request.post_data_json)
                if len(requests) == 1:
                    route.fulfill(status=502, content_type='application/json', body=json.dumps({
                        'success': False, 'error': 'Gemini is temporarily unavailable.', 'can_use_faq': True,
                    }))
                else:
                    route.continue_()

            page.route('**/api/chat', transient)
            ask('What programs does CCIT offer?')
            expect(page.get_by_role('button', name='Retry', exact=True)).to_be_visible()
            expect(page.get_by_role('button', name='Read FAQ answer instead')).to_be_visible()
            page.locator('#question').fill('Keep this draft')
            page.get_by_role('button', name='Retry', exact=True).click()
            expect(page.locator('.message.assistant .message-text')).to_contain_text('Bachelor of Science in Computer Science (BSCS)')
            expect(page.locator('.message.error')).to_have_count(0)
            expect(page.locator('.message.user')).to_have_count(1)
            assert len(requests) == 2 and requests[0] == requests[1]
            assert page.locator('#question').input_value() == 'Keep this draft'
            passed('Retry preserves question/context/draft and replaces error without duplicate user messages')

            home()
            requests = []

            def unavailable_until_faq(route):
                body = route.request.post_data_json
                requests.append(body)
                if body.get('mode') == 'faq':
                    route.continue_()
                else:
                    route.fulfill(status=502, content_type='application/json', body=json.dumps({
                        'success': False, 'error': 'Gemini is temporarily unavailable.', 'can_use_faq': True,
                    }))

            page.route('**/api/chat', unavailable_until_faq)
            ask('What programs does CCIT offer?')
            page.get_by_role('button', name='Read FAQ answer instead').click()
            expect(page.locator('.message-mode')).to_have_text('FAQ retrieval only · not AI generated')
            expect(page.locator('.message.assistant .message-text')).to_contain_text('Bachelor of Science in Computer Science (BSCS)')
            expect(page.locator('.message.user')).to_have_count(1)
            expect(page.locator('.message.error')).to_have_count(0)
            assert requests[-1]['mode'] == 'faq'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            passed('Explicit FAQ fallback sends mode=faq and labels the real source answer')

            home()
            attempts = []

            def old_turn_failure(route):
                body = route.request.post_data_json
                attempts.append(body)
                if len(attempts) == 1:
                    route.fulfill(status=502, content_type='application/json', body=json.dumps({
                        'success': False, 'error': 'Temporary failure', 'can_use_faq': True,
                    }))
                else:
                    route.continue_()

            page.route('**/api/chat', old_turn_failure)
            ask('What is BSCS?')
            ask('What is BSIT?')
            page.get_by_role('button', name='Retry', exact=True).click()
            expect(page.locator('.message.error')).to_have_count(0)
            ask('What jobs can I get after this program?')
            expect(page.locator('.message.assistant').last.locator('.message-text')).to_contain_text('Network Administrator')
            passed('Retrying an old turn preserves the newer program context')

            home()
            attack = '<img src=x onerror="window.ccitInjected=1">'
            page.route('**/api/chat', lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps({
                'success': True, 'reply': '**Important**\n• **' + attack + '**\n1. **Numbered fact**\nUnmatched ** stays literal.',
                'mode': 'ai', 'context': {'programs': []},
                'sources': [{'id': 'TEST', 'title': 'Synthetic safety fixture', 'source': 'Fixture', 'currency_status': 'unconfirmed'}],
                'details': [{'id': 'TEST', 'answer': attack}], 'warnings': [attack],
            })))
            ask('**Safety fixture**')
            reply = page.locator('.message.assistant').last
            expect(reply.locator('.message-text strong')).to_have_text(['Important', attack, 'Numbered fact'])
            expect(reply.locator('.message-text ul li strong')).to_have_text(attack)
            expect(reply.locator('.message-text ol li strong')).to_have_text('Numbered fact')
            expect(reply.locator('.message-text')).to_contain_text('Unmatched ** stays literal.')
            expect(page.locator('.message.user .message-text')).to_have_text('**Safety fixture**')
            expect(page.locator('.message.user strong, .source-warning, .source-details, .message-sources')).to_have_count(0)
            assert page.locator('.message img').count() == 0
            assert page.evaluate('window.ccitInjected === undefined')
            passed('AI bold/list rendering is safe, unmatched markers and user text stay literal, and metadata stays hidden')

            assert not errors, errors
        finally:
            context.close()
            browser.close()
    report = {'executed_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'FAQ answers from the running app; simulated provider errors/safety fixture; no live AI calls',
              'checks': results}
    (args.output / 'browser-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(results)} improvement browser scenarios passed')


if __name__ == '__main__':
    main()
