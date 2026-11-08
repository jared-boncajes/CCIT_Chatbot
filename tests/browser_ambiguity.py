"""Real UI checks against a FAQ-mode server.

Install Playwright separately, then run:
python tests/browser_ambiguity.py --base-url http://127.0.0.1:5000
Uses system Chromium; screenshots are written outside the checkout.
"""
import argparse
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:5000')
    parser.add_argument('--output', type=Path, default=Path('/tmp/ccit-ambiguity'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        for width in (390, 1280):
            context = browser.new_context(viewport={'width': width, 'height': 900})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(args.base_url)
            expect(page.locator('.topic-card').first).to_be_enabled()

            def ask(question):
                page.locator('#question').fill(question)
                with page.expect_response(lambda r: r.url.endswith('/api/chat') and r.request.method == 'POST') as response:
                    page.locator('#question').press('Enter')
                data = response.value.json()
                expect(page.locator('.typing')).to_have_count(0)
                expect(page.locator('#clear')).to_be_enabled()
                return data

            first = ask('prerequisites')
            assert first['mode'] == 'clarification' and first['sources'] == []
            expect(page.locator('.message.assistant').last).to_contain_text('Which subject')
            assert 'CSAL102' not in page.locator('.message.assistant').last.inner_text()
            page.screenshot(path=str(args.output / f'clarification-{width}.png'), full_page=True)
            second = ask('ITECC03')
            assert second['mode'] == 'clarification'
            expect(page.locator('.message.assistant').last).to_contain_text('Which program')
            final = ask('BSCS')
            assert [s['id'] for s in final['sources']] == ['FAQ-030']
            expect(page.locator('.message.assistant').last).to_contain_text('ITECC02')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors, errors
            print(f'PASS {width}px: clarification, course reply, program reply, correct answer, no overflow or JS errors')
            context.close()
        browser.close()


if __name__ == '__main__':
    main()
