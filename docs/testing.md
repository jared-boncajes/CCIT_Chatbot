# Validation evidence

Executed November 4, 2026: `.venv/bin/python -m pytest -q` — **53 passed**.

19 implementation checks cover invalid input, synthetic retrieval variants, unknown questions, privacy, missing data/key, pending-record exclusion, simulated provider failure and frontend delivery. An additional 34 questions exercise the actual uploaded source with expected first source IDs or fallback/privacy behavior. All 34 passed. Actual returned answers, expected/actual IDs and elapsed times are recorded in `evaluation.json`. This is an automated retrieval evaluation in explicitly labeled FAQ mode, not an AI answer accuracy measurement or independent fact verification.

The HTTP smoke test before import returned HTML 200, health 200 with ready=false and chat 503 for missing data. A subsequent FAQ-mode HTTP test is recorded below after restart. No live provider request or browser-responsive/screenshot check has been executed. Python dependency consistency and JavaScript syntax checks passed.

After import and restart, live HTTP requests passed: health reported ready=true, 22 records and FAQ mode; a programs question returned HTTP 200 with FAQ-006; an unsupported meeting question returned HTTP 200 with a source-free fallback. Live AI remains untested.
