# CCIThink

Flask and vanilla JavaScript foundation for the FAITH Colleges CCIT information assistant. Students ask questions, a conservative retriever selects reviewed JSON records, and the official Google Gen AI or OpenAI SDK generates a grounded answer. No database or frontend build is required.

**Status: source-grounded FAQ mode and the revised Figma interface work; live AI remains untested.** All 22 FAQs from the uploaded About CCIT.pdf are imported. Source extraction is verified, but institutional currency is unconfirmed; see `docs/source-review.md`. This cloud checkout has an ignored `.env` explicitly selecting FAQ retrieval-only mode. Set `CHAT_MODE=ai` and a valid key to enable actual generation. Live AI has not been tested.

The uploaded Figma scene graph was decoded and its visible **Revised Version** frame inspected at full size. The interface uses its Inter fonts, red gradient, layout measurements, original logo/portrait, and original vector icons. Three topic cards open questions from the source document. The profile chip supports optional name personalization within the browser tab; it is not authentication. See [design notes](docs/design.md), [desktop screenshot](docs/screenshots/desktop.png), and [mobile screenshot](docs/screenshots/mobile.png).

## Windows / VS Code setup

Open this folder in VS Code. In PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
code .env
```

The private **`.env` file belongs in the project root, beside `app.py` and `requirements.txt`**. In VS Code's Explorer, right-click the `CCIT_Chatbot` folder and select **New File** if you need to create it. Name it exactly `.env`, including the leading dot and without `.txt`.

For a Gemini key created in Google AI Studio, put these settings in `.env` (replace the placeholder privately):

```dotenv
CHAT_MODE=ai
CCIT_AI_PROVIDER=gemini
GEMINI_API_KEY=paste_your_gemini_key_here
CCIT_MODEL=gemini-3.8-flash
```

`CCIT_MODEL` is configurable. The default above follows the current Google SDK examples; select an available model API ID in AI Studio for your own project. Free-tier eligibility and quotas depend on the model/project. A key alone does not guarantee an available free quota.

Save `.env`, install the updated dependencies if you already had an earlier checkout, then start or restart Flask:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Keep the key in `.env`, which is excluded by `.gitignore`; `.env.example` contains placeholders for sharing. If `.env` already exists, edit its matching entries instead of overwriting it or appending duplicate entries. Keep keys out of frontend JavaScript, chat and GitHub.

For OpenAI, set `CCIT_AI_PROVIDER=openai`, `CCIT_API_KEY` to your OpenAI key, and `CCIT_MODEL` to a model available to your account (default `gpt-4.1-mini`). Existing OpenAI installations remain compatible when `CCIT_AI_PROVIDER` is omitted. A Gemini key is read only for the Gemini provider; an OpenAI key is read only for the OpenAI provider. For cloud tasks, use secure environment settings instead of chat; Gemini requests require `generativelanguage.googleapis.com` network access.

Alternatively set `CHAT_MODE=faq` to explicitly use retrieval-only responses, labeled in the UI. This mode still requires reviewed knowledge. Never treat it as AI generation. Process environment settings take precedence over `.env`; restart Flask after changing either.

For Linux/cloud, use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python app.py`. Run from this directory. Flask listens on port 5000 with debug disabled. This is a development server; public deployment requires a production WSGI server and deployment configuration.

## Knowledge maintenance

All 22 FAQ pairs from the uploaded About CCIT.pdf are in `data/knowledge.json`. Preserve the original meaning when updating them. Records contain `id`, `category`, `question`, `answer`, `keywords`, `source`, `verification_status`, `verification_scope`, `currency_status`, and `reviewed_at`. Use `pending` until an entry has been checked against its source; only `verified` records are retrieved. Here, `verified` means faithful source extraction, while `currency_status=unconfirmed` explicitly records that current institutional accuracy has not been independently confirmed. A department reviewer should confirm current details before they are presented as current policy. Review dean/faculty assignments, scholarships, accreditation and program offerings for currency; document discrepancies rather than inventing corrections. Restart the server after editing JSON.

The retriever normalizes words, includes limited Filipino/English aliases and spelling tolerance, and requires 60% query-term coverage. It is deliberately small and has limitations with complex or ambiguous questions. Evaluate and tune against the real FAQs before demonstration. Model grounding instructions reduce unsupported claims but do not guarantee correctness; review actual provider answers.

## API

- `GET /api/health`: process availability, record counts, mode and readiness; HTTP 200 does not imply content readiness.
- `GET /api/suggestions`: questions from verified records, grouped into the three design topics. Topic notes identify information absent from the document.
- `POST /api/chat`: JSON object with `message` (1–1,000 characters). Success returns `success`, `reply`, `sources`, `mode`. Invalid input returns 400, missing configuration 503, provider failure 502.

Private-record questions receive a privacy response. Unknown questions get a source-free fallback. Messages are rendered as text, never inserted as HTML. API keys stay on the backend. Requests have frontend and SDK timeouts; failed requests remain retryable. Clear chat removes the current in-memory conversation. History is not persisted or sent to the model.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

Linux: `.venv/bin/python -m pytest -q`. Optional browser checks use Playwright and Chromium: install Playwright separately (`python -m pip install playwright`, then `python -m playwright install chromium` if no Chromium is installed), start the app in FAQ mode, and run `python tests/browser_smoke.py`. This captures screenshots and checks six viewport sizes, suggestions, real requests, loading, privacy/fallback responses, dialogs, and simulated errors. See `docs/testing.md` for executed results and unrun checks. Test records are explicitly synthetic and are never loaded by the application.

## Remaining work

Confirm source currency with CCIT, review the recorded 34 source-question evaluation, and test live AI with valid credentials. Desktop, tablet and mobile Chromium checks and actual screenshots are complete; Safari, Firefox, real mobile devices and screen-reader behavior have not been tested. The supplied file contains no visible conversation/error/mobile frames; these states use the same design system. This is not a claim of an exact pixel match or independently verified answer accuracy. Gemini and OpenAI provider integrations have been tested with in-memory SDK transports, but neither has been verified with a live key. Future improvements include stronger multilingual retrieval, review-date enforcement, deployment rate limits and contextual follow-ups.
