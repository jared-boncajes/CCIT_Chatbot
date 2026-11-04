"""Optional browser checks against a running FAQ-mode server.

Install Playwright separately; it is not an application dependency. This script
uses real source answers. Only the explicitly named error checks mock responses.
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
    parser.add_argument('--output', type=Path, default=Path('docs/screenshots'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []

    def passed(name, **details):
        results.append({'check': name, 'passed': True, **details})
        print('PASS', name, flush=True)

    def no_overflow(page):
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow'

    def finish_reply(page):
        expect(page.locator('.typing')).to_have_count(0)
        expect(page.locator('#clear')).to_be_enabled()

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium, headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        try:
            health = browser.new_context().request.get(args.base_url + '/api/health').json()
            assert health['ready'] and health['mode'] == 'faq', 'Start the server with CHAT_MODE=faq and loaded knowledge first'
            for name, width, height in [
                ('desktop', 1440, 1024), ('laptop', 1280, 800),
                ('tablet', 768, 1024), ('mobile', 390, 844),
                ('small-mobile', 320, 568), ('landscape', 844, 390),
            ]:
                context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(args.base_url)
                expect(page.locator('.topic-card').first).to_be_enabled()
                expect(page.locator('#status')).to_contain_text('FAQ mode')
                page.evaluate('document.fonts.ready')
                no_overflow(page)
                assert page.evaluate("document.fonts.check('500 48px Inter')"), 'Inter font not loaded'
                expect(page.locator('#send')).to_be_disabled()
                if name == 'desktop':
                    box = page.locator('#chat').bounding_box()
                    assert abs(box['width'] - 910) < 1
                    assert abs(box['y'] - 516) < 3
                    assert abs(box['height'] - 84) < 1
                if name in ('desktop', 'tablet', 'mobile'):
                    page.screenshot(path=str(args.output / f'{name}.png'), full_page=True)
                for button in page.locator('.topic-card').all():
                    button.click()
                    expect(page.locator('#question-panel')).to_be_visible()
                    assert page.locator('#question-list button').count() > 0
                    no_overflow(page)
                    button.click()
                    expect(page.locator('#question-panel')).to_be_hidden()
                page.locator('#question').fill('What programs does CCIT offer?')
                page.locator('#question').press('Enter')
                expect(page.locator('.message-sources')).to_contain_text('FAQ-006')
                finish_reply(page)
                no_overflow(page)
                if name == 'mobile':
                    page.screenshot(path=str(args.output / 'mobile-conversation.png'), full_page=True)
                assert not errors, errors
                passed(f'{name}: layout, all topic selectors, and real sourced answer', viewport=f'{width}x{height}')
                context.close()

            context = browser.new_context(viewport={'width': 1440, 'height': 1024}, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(args.base_url)
            expect(page.locator('.topic-card').first).to_be_enabled()

            page.get_by_role('button', name='Personalize your greeting').click()
            expect(page.locator('#name-dialog')).to_be_visible()
            page.locator('#preferred-name').fill('  Test   Student  ')
            page.get_by_role('button', name='Save name').click()
            expect(page.locator('#greeting')).to_have_text('Hello, Test Student!')
            page.reload()
            expect(page.locator('#greeting')).to_have_text('Hello, Test Student!')
            page.get_by_role('button', name='Personalize your greeting').click()
            page.keyboard.press('Escape')
            expect(page.locator('#name-dialog')).to_be_hidden()
            page.get_by_role('button', name='Personalize your greeting').click()
            page.locator('#preferred-name').fill('')
            page.get_by_role('button', name='Save name').click()
            expect(page.locator('#profile-name')).to_have_text('Guest')
            passed('Optional name personalization, tab persistence, Escape, and guest reset')

            page.locator('#question').fill('   ')
            expect(page.locator('#send')).to_be_disabled()
            page.locator('#question').press('Enter')
            expect(page.locator('.message')).to_have_count(0)
            page.locator('#question').fill('first line')
            page.locator('#question').press('Shift+Enter')
            assert page.locator('#question').input_value().endswith('\n')
            expect(page.locator('.message')).to_have_count(0)
            page.locator('#question').fill('')
            passed('Empty/whitespace protection and Shift+Enter multiline input')

            # Hold the real backend request until loading and duplicate protection
            # have been inspected. No synthetic answer is substituted.
            pending = []
            page.route('**/api/chat', lambda route: pending.append(route))
            page.locator('[data-topic="academics"]').click()
            page.locator('#question-list').get_by_role('button', name='What programs does CCIT offer?', exact=True).click()
            expect(page.locator('.typing')).to_be_visible()
            expect(page.locator('#send')).to_be_disabled()
            expect(page.locator('#clear')).to_be_disabled()
            page.locator('#question').fill('duplicate attempt')
            page.locator('#question').press('Enter')
            assert len(pending) == 1
            page.screenshot(path=str(args.output / 'loading.png'))
            page.locator('#question').fill('')
            pending[0].continue_()
            expect(page.locator('.message-sources')).to_contain_text('FAQ-006')
            expect(page.locator('.message-mode')).to_have_text('FAQ retrieval only · not AI generated')
            finish_reply(page)
            page.unroute('**/api/chat')
            page.screenshot(path=str(args.output / 'conversation.png'))
            passed('Suggestion submission, real source answer, FAQ disclosure, typing, and duplicate protection')

            page.locator('#clear').click()
            expect(page.locator('#clear-dialog')).to_be_visible()
            page.get_by_role('button', name='Keep chatting').click()
            expect(page.locator('.message')).to_have_count(2)
            page.locator('#clear').click()
            page.locator('#confirm-clear').click()
            expect(page.locator('.message')).to_have_count(0)
            expect(page.locator('#welcome')).to_be_visible()
            expect(page.locator('.topic-card').first).to_have_attribute('aria-expanded', 'false')
            passed('New-chat confirmation, cancellation, and complete UI reset')

            for question, expected in [
                ('When is tomorrow meeting?', "don't currently have verified information"),
                ('What are my grades?', 'cannot access private student records'),
            ]:
                page.locator('#question').fill(question)
                page.locator('#question').press('Enter')
                expect(page.locator('.message.assistant').last).to_contain_text(expected)
                finish_reply(page)
            passed('Real unsupported-question fallback and private-record response')

            attack = '<img src=x onerror="window.ccitXss=1">'
            page.locator('#question').fill(attack)
            page.locator('#question').press('Enter')
            expect(page.locator('.message.user').last.locator('.message-text')).to_have_text(attack)
            finish_reply(page)
            assert page.locator('.message.user img').count() == 0
            assert page.evaluate('window.ccitXss === undefined')
            passed('User text is rendered literally without HTML execution')

            page.route('**/api/chat', lambda route: route.fulfill(status=502, content_type='application/json', body=json.dumps({
                'success': False, 'error': 'The AI service is unavailable. Please try again shortly.',
            })))
            page.locator('#question').fill('What programs does CCIT offer?')
            page.locator('#question').press('Enter')
            expect(page.locator('.message.error').last).to_contain_text('AI service is unavailable')
            finish_reply(page)
            page.unroute('**/api/chat')
            page.locator('#question').fill('What programs does CCIT offer?')
            page.locator('#question').press('Enter')
            expect(page.locator('.message.assistant').last.locator('.message-sources')).to_contain_text('FAQ-006')
            finish_reply(page)
            passed('Simulated provider error display and successful real retry')
            assert not errors, errors
            context.close()

            context = browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
            page = context.new_page()
            page.route('**/api/suggestions', lambda route: route.fulfill(status=503, content_type='application/json', body='{}'))
            page.goto(args.base_url)
            expect(page.locator('.topic-card').first).to_be_disabled()
            page.locator('#question').fill('What programs does CCIT offer?')
            page.locator('#question').press('Enter')
            expect(page.locator('.message-sources')).to_contain_text('FAQ-006')
            finish_reply(page)
            passed('Simulated suggestions outage leaves typed questions functional')
            context.close()
        finally:
            browser.close()

    report = {'executed_at': datetime.now(timezone.utc).isoformat(), 'mode': 'FAQ retrieval only; no live AI calls', 'checks': results}
    (args.output / 'browser-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(results)} browser checks passed; evidence saved to {args.output}')


if __name__ == '__main__':
    main()
