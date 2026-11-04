# CCITthink

Flask and vanilla JavaScript foundation for the FAITH Colleges CCIT information assistant. Students ask questions, a conservative retriever selects reviewed JSON records, and the official OpenAI SDK generates a grounded answer. No database or frontend build is required.

**Status: source-grounded FAQ mode works; live AI and exact design validation remain incomplete.** All 22 FAQs from the uploaded About CCIT.pdf are imported. Source extraction is verified, but institutional currency is unconfirmed; see `docs/source-review.md`. This cloud checkout has an ignored `.env` explicitly selecting FAQ retrieval-only mode. Set `CHAT_MODE=ai` and a valid key to enable actual generation. Live AI has not been tested.

The Figma archive thumbnail was inspected; individual frames, exact fonts, assets and additional states have not been inspected. The responsive HTML follows the visible red header, centered greeting and message field, with dataset-driven suggestion cards. The personalized account chip is omitted because no authentication is implemented.

## Windows / VS Code setup

Open this folder in VS Code. In PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python app.py
```

Edit `.env` locally: set `CCIT_API_KEY` to your OpenAI key and `CCIT_MODEL` to a model available to your account. Never commit `.env`. Alternatively set `CHAT_MODE=faq` to explicitly use retrieval-only responses, labeled in the UI. This mode still requires reviewed knowledge. Never treat it as AI generation.

For Linux/cloud, use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python app.py`. Run from this directory. Flask listens on port 5000 with debug disabled. This is a development server; public deployment requires a production WSGI server and deployment configuration.

## Knowledge maintenance

Obtain the entire About CCIT document from the supplied Google Docs source. Extract every FAQ pair and preserve the original meaning. Populate `data/knowledge.json` with a JSON list of records containing `id`, `category`, `question`, `answer`, `keywords`, `source`, `verification_status`, and a `reviewed_at` date. Use `pending` until a department reviewer confirms each answer. Only `verified` records are retrieved. Review dean/faculty assignments, scholarships, accreditation and program offerings for currency; document discrepancies rather than inventing corrections. Restart the server after editing JSON.

The retriever normalizes words, includes limited Filipino/English aliases and spelling tolerance, and requires 60% query-term coverage. It is deliberately small and has limitations with complex or ambiguous questions. Evaluate and tune against the real FAQs before demonstration. Model grounding instructions reduce unsupported claims but do not guarantee correctness; review actual provider answers.

## API

- `GET /api/health`: process availability, record counts, mode and readiness; HTTP 200 does not imply content readiness.
- `GET /api/suggestions`: questions from verified records.
- `POST /api/chat`: JSON object with `message` (1–1,000 characters). Success returns `success`, `reply`, `sources`, `mode`. Invalid input returns 400, missing configuration 503, provider failure 502.

Private-record questions receive a privacy response. Unknown questions get a source-free fallback. Messages are rendered as text, never inserted as HTML. API keys stay on the backend. Requests have frontend and SDK timeouts; failed requests remain retryable. Clear chat removes the current in-memory conversation. History is not persisted or sent to the model.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

Linux: `.venv/bin/python -m pytest -q`. See `docs/testing.md` for executed results and unrun checks. Test records are explicitly synthetic and are never loaded by the application.

## Remaining work

Confirm source currency with CCIT, decode or obtain full Figma frame exports and implement exact assets, review the recorded 34 source-question evaluation, test live AI, inspect mobile/tablet/desktop in a browser, and capture actual screenshots. No accuracy percentage or design-fidelity claim is available yet. Provider selection currently supports OpenAI via the maintained SDK; Gemini is not implemented. Future improvements include stronger multilingual retrieval, review-date enforcement, deployment rate limits and contextual follow-ups.
