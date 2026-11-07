# Validation evidence

Executed November 7, 2026: `.venv/bin/python -m pytest -q` — **66 passed**.

20 implementation checks cover invalid input, synthetic retrieval variants, unknown questions, privacy, missing data/key, pending-record exclusion, simulated provider failure, frontend delivery and reviewed source-only topic suggestions. Another 34 questions exercise the actual uploaded source with expected first source IDs or fallback/privacy behavior. All 34 passed. Actual returned answers, expected/actual IDs and elapsed times are recorded in `evaluation.json`. This is retrieval evaluation in explicitly labeled FAQ mode, not a live AI answer evaluation or independent fact verification.

12 additional provider checks use synthetic records and in-memory HTTP transports with the official SDKs. They verify Gemini request serialization, source/system instructions, response parsing and timeout; empty/blocked responses; quota errors without retry or secret disclosure; the existing OpenAI Responses API; provider-specific key selection/default models; and invalid-provider reporting. These are offline integration tests, not successful live AI calls.

## Browser validation

On November 4, `python tests/browser_smoke.py` against the running FAQ-mode Flask server passed **14 browser scenarios** in system Chromium using Playwright. The script and its result JSON preserve the exact checks; related assertions are grouped within each scenario rather than counted as individual tests. These checks were not repeated for the November 7 backend/provider change.

- 1440×1024 desktop, 1280×800 laptop, 768×1024 tablet, 390×844 mobile, 320×568 small mobile and 844×390 landscape: no horizontal document overflow; all three topic selectors open/close; questions reach Flask and receive source FAQ-006.
- Desktop composer geometry: 910×84 pixels, y≈516; self-hosted Inter loads.
- Optional name personalization, tab persistence, Escape dismissal and clearing the preferred name.
- Empty/whitespace send prevention and Shift+Enter multiline input.
- A source question selected through the topic panel, actual source reply, FAQ disclosure, typing feedback and duplicate submission prevention while the real request is held pending.
- New-chat confirmation, cancel and reset.
- Real unknown-question fallback and private-record response.
- Literal rendering of HTML-like user input without execution.
- A simulated provider HTTP 502 followed by a successful real retry.
- A simulated suggestions outage while typed questions still work.

No JavaScript page errors occurred in the normal and interaction scenarios. The two intentional outage checks use mocked failures; they are not live provider tests. Screenshots of the actual application and the timestamped browser report are in `docs/screenshots/`. See `design.md` for the source-frame inspection, implementation details and acknowledged adaptations.

## Other checks and limitations

JavaScript syntax, Python dependency consistency and Git whitespace checks passed. HTTP smoke tests confirmed HTML/health delivery, missing-data errors before import, and sourced FAQ replies/fallback after import. No live provider request has succeeded because an API key has not been supplied. Firefox, Safari, real mobile devices, assistive technology and production deployment/load testing remain unrun.
