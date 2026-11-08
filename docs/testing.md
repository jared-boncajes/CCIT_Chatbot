# Validation evidence

The latest automated run completed with **240 passed** (`.venv/bin/python -m pytest -q`). It covers the original 94 checks and 146 regression checks for the reviewed question variants, additional English/Tagalog phrasing, unsupported facts, direct summaries and bold key facts, backend source metadata, context/clarification validation, explicit FAQ override, privacy handling and provider-free recovery. No test uses a real AI credential.

## Actual HTTP question evaluation

`python tests/evaluate_questions.py --base-url <local FAQ server>` completed **95/95** expected source-support or mode checks:

| Group | Passed | Total |
| --- | ---: | ---: |
| Original source questions | 22 | 22 |
| Review student phrasing/multi-topic requests | 33 | 33 |
| Additional wording variations | 22 | 22 |
| Unsupported questions | 12 | 12 |
| Explicit privacy responses | 6 | 6 |

Actual replies, selected source IDs, modes, warnings and timings are recorded in evaluation-improved.json. The review phrasing set improved from 8 expected-source matches to 33; it was used during development and is not an independent accuracy benchmark. These checks verify source support and handling, not current institutional accuracy or live AI response quality. Extra automated negative controls cover undocumented fees, online delivery, scholarship guarantees, dates, office details and unsupported programs.

## Browser validation

`python tests/browser_smoke.py` passed **14 scenarios** in Chromium at desktop 1440×1024, laptop 1280×800, tablet 768×1024, mobile 390×844, small mobile 320×568 and landscape 844×390. Checks include geometry, font loading, no horizontal document overflow, all topic selectors, actual sourced replies, personalization/dialogs, empty-input and duplicate protection, loading, clear-chat confirmation, private/unknown questions, literal HTML-like user text, and simulated outages/retry.

`python tests/browser_improvements.py` passed **6 additional scenarios**:

1. Direct answer, bold key fact, absence of source/verification clutter and actual plain-text clipboard copy.
2. Program follow-up, New chat context reset and completing a program clarification.
3. Retry with original request/context, no duplicate user message and preservation of an unsent draft.
4. Explicit mode=faq fallback, labeled source answer and replacement of the error.
5. Retrying an older turn while preserving the newer program context.
6. Safe bold/list rendering for AI replies, literal unmatched markers and user text, and hidden source metadata.

Successful source replies come from the actual local Flask server in FAQ mode. Provider failures and safety payloads are deliberately simulated; they are not live AI responses. No unexpected JavaScript page errors occurred. Current screenshots and timestamped reports are in screenshots/ and screenshots/improvements/.

## Provider and diagnostic coverage

SDK tests use real SDK serialization/parsing with in-memory HTTP transports. They exercise Gemini/OpenAI grounding payloads, default models/key selection, source-only replies, empty/blocked results, quotas without retries, safe classification/logging of 400/403/404/429/503 and connection/timeout errors, model listing and secret-free CLI output. Model-finder tests cover the three-request cap, early success, exclusion of media/preview/Pro IDs, immediate stop on quota/access/connection errors and preservation of .env.

No successful live generation has been confirmed here. The user separately reported a live 503 for gemini-3.8-flash and 404 for the listed gemini-2.5-flash-lite. The model finder remains available to test actual per-project generation access locally.

## Limits

Source transcription is checked against the supplied PDF; current department facts remain unconfirmed. Firefox, Safari, actual mobile devices, screen readers, deployment/load testing and broad held-out language evaluation remain unrun. JavaScript syntax and Git whitespace checks passed. No application dependencies or lockfiles were changed by the improvements.
