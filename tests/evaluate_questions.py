"""Record actual HTTP answers for the source-supported FAQ regression questions."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:5000')
    parser.add_argument('--output', type=Path, default=Path('test-results/questions.json'))
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    with urlopen(base + '/api/health', timeout=10) as response:
        health = json.load(response)
    if health.get('mode') != 'faq' or not health.get('ready'):
        raise SystemExit('Run a ready FAQ-mode server first; this evaluator must not consume live AI quota.')
    cases = json.loads((Path(__file__).parent / 'fixtures/student_questions.json').read_text())
    results = []
    for case in cases:
        started = perf_counter()
        request = Request(base + '/api/chat', data=json.dumps({'message': case['question']}).encode(),
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
            status = response.status
        actual = {source['id'] for source in data.get('sources', [])}
        expected = set(case.get('expected_sources', []))
        passed = (data.get('mode') == case['expected_mode']) if 'expected_mode' in case else (
            expected <= actual if case.get('all_required') else bool(expected & actual))
        results.append({**case, 'http_status': status, 'actual_mode': data.get('mode'),
                        'actual_sources': sorted(actual), 'reply': data.get('reply'),
                        'warnings': data.get('warnings', []), 'passed': passed,
                        'elapsed_ms': round((perf_counter() - started) * 1000, 2)})
    summary = {group: {'passed': sum(r['passed'] for r in results if r['group'] == group),
                       'total': sum(r['group'] == group for r in results)} for group in sorted({r['group'] for r in results})}
    report = {'executed_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'Actual HTTP requests in labeled FAQ mode; no live AI calls',
              'scope': 'Expected source support or fallback/privacy behavior; not independent fact verification or a general accuracy estimate.',
              'summary': summary, 'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=2))
    print(f'{sum(r["passed"] for r in results)}/{len(results)} source-support checks passed; results saved to {args.output}')
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
