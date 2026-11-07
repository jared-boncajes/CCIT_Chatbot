# CCIThink

Flask and vanilla JavaScript foundation for the FAITH Colleges CCIT information assistant. Students ask questions, a conservative retriever selects reviewed JSON records, and the official Google Gen AI or OpenAI SDK generates a grounded answer. No database or frontend build is required.

**Status: source-grounded FAQ mode, short follow-ups, and the revised Figma interface work. Successful live AI generation remains unverified here.** All 22 FAQs from the uploaded About CCIT.pdf are imported. Source extraction is verified, but institutional currency is unconfirmed; see `docs/source-review.md` and the [department confirmation checklist](docs/department-verification.md). This cloud checkout has an ignored `.env` explicitly selecting FAQ retrieval-only mode. Set `CHAT_MODE=ai` and a valid key to enable actual generation.

The uploaded Figma scene graph was decoded and its visible **Revised Version** frame inspected at full size. The interface uses its Inter fonts, red gradient, layout measurements, original logo/portrait, and original vector icons. Three topic cards open questions from the source document. The profile chip supports optional name personalization within the browser tab; it is not authentication. See [design notes](docs/design.md), [desktop screenshot](docs/screenshots/desktop.png), and [mobile screenshot](docs/screenshots/mobile.png).

Question matching includes English/Tagalog aliases, full program names and close intent-word typos. FAQ answers focus on the question, with readable lists, a visible source-currency warning, expandable original source text and Copy answer. A short program context supports follow-ups such as “What jobs can I get after this program?” New chat clears that context. AI errors offer Retry and an explicitly labeled Read FAQ answer instead action; FAQ fallback never calls an AI provider or changes the server's configured mode.

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

`CCIT_MODEL` is configurable. The name above is an SDK example, not a model verified for your own Google project. After adding your key, use `check_ai.py --find-model` to test up to three listed stable Flash/Flash-Lite text models and stop at the first usable response. It prints the exact `CCIT_MODEL` line to copy into `.env`; it never changes the file. Free-tier eligibility and quotas depend on the model/project. A listed model or an API key alone does not guarantee available free quota.

Save `.env`, install the updated dependencies if you already had an earlier checkout, then start or restart Flask:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python check_ai.py --find-model
```

If the test succeeds, copy its `CCIT_MODEL=...` line into `.env`, save, and start Flask. If all tested models fail, read the diagnostic codes before changing more settings:

```powershell
.venv\Scripts\python app.py
```

Keep the key in `.env`, which is excluded by `.gitignore`; `.env.example` contains placeholders for sharing. If `.env` already exists, edit its matching entries instead of overwriting it or appending duplicate entries. Keep keys out of frontend JavaScript, chat and GitHub.

For OpenAI, set `CCIT_AI_PROVIDER=openai`, `CCIT_API_KEY` to your OpenAI key, and `CCIT_MODEL` to a model available to your account (default `gpt-4.1-mini`). Existing OpenAI installations remain compatible when `CCIT_AI_PROVIDER` is omitted. A Gemini key is read only for the Gemini provider; an OpenAI key is read only for the OpenAI provider. For cloud tasks, use secure environment settings instead of chat; Gemini requests require `generativelanguage.googleapis.com` network access.

Alternatively set `CHAT_MODE=faq` to explicitly use retrieval-only responses, labeled in the UI. This mode still requires reviewed knowledge. Never treat it as AI generation. Process environment settings take precedence over `.env`; restart Flask after changing either.

For Linux/cloud, use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python app.py`. Run from this directory. Flask listens on port 5000 with debug disabled. This is a development server; public deployment requires a production WSGI server and deployment configuration.

## AI troubleshooting

If a chat answer fails, the interface now distinguishes key/project access, unavailable models, quota/rate limits, timeouts, connection failures, rejected requests and empty results. Flask logs contain a fixed diagnostic code and upstream status, not raw provider exceptions or credentials.

Run diagnostics from the project root with the same virtual-environment Python that runs Flask:

```powershell
.venv\Scripts\python check_ai.py
.venv\Scripts\python check_ai.py --list-models
.venv\Scripts\python check_ai.py --test
.venv\Scripts\python check_ai.py --find-model
```

The first command checks configuration without contacting an AI provider. Model listing uses your configured key for a read-only API request and prints compatible IDs (for Gemini, those supporting generateContent). `--test` makes one actual generation request with retrieved source context, even if normal chat is in FAQ mode. None of the diagnostic commands prints the key or a raw provider error. If the virtual environment folder has another name, such as `ccit_chatbot`, replace `.venv` in these commands with that folder name.

`--find-model` is an explicit Gemini-only test that lists models, selects at most three stable Flash/Flash-Lite text IDs, prefers recent Flash-Lite versions, and tries one grounded request per candidate. It stops at the first success and prints the working ID without modifying `.env`. It continues to another model only after model absence, temporary provider unavailability or an empty response. It stops immediately on quota, key/access, request-configuration or connection failures. These requests consume API quota under the project's existing terms; the command does not enable billing or guarantee free usage. It excludes image, preview, research and Pro model IDs. The normal chatbot still uses the one explicitly configured model; it does not silently switch providers/models.

- `ai_model_unavailable`: listing can include a model whose generation request fails. Run `--find-model` to test actual generation, then use its successful `CCIT_MODEL` line and restart Flask. An SDK example ID may not be available to your project.
- `ai_access_denied`: check the private key and its project/API restrictions in the provider console.
- `ai_quota_exceeded`: check the model/project allowance. Wait for an applicable rate-limit reset; model listing does not establish free quota.
- `ai_sdk_configuration`: reinstall `requirements.txt` using the same virtual-environment Python, then restart Flask.
- `ai_connection_failed` / `ai_timeout`: check server internet access, firewall/proxy settings, TLS trust and provider availability. Keep certificate verification enabled.

Share only the diagnostic code/status or model IDs when requesting help. Keep the actual key in your private `.env`.

## Knowledge maintenance

All 22 FAQ pairs from the uploaded About CCIT.pdf are in `data/knowledge.json`. Preserve the original meaning when updating them. Records contain `id`, `category`, `question`, `answer`, `keywords`, `source`, `verification_status`, `verification_scope`, `currency_status`, and `reviewed_at`. Use `pending` until an entry has been checked against its source; only `verified` records are retrieved. Here, `verified` means faithful source extraction, while `currency_status=unconfirmed` explicitly records that current institutional accuracy has not been independently confirmed. A department reviewer should confirm current details before they are presented as current policy. Review dean/faculty assignments, scholarships, accreditation and program offerings for currency; document discrepancies rather than inventing corrections. Restart the server after editing JSON.

The retriever normalizes phrases and word forms, identifies topic/program intent, and scores question/keyword/answer terms with a minimum coverage threshold. It preserves named scholarships instead of treating every “course” as a degree, and can retrieve separate sources for multi-topic questions. Checks for unsupported fees, dates, contact details and other facets prevent a broad topic match from establishing a missing fact. Only records marked verified against their source are eligible. Word normalization uses a bounded in-memory cache; conversations and generated answers are not cached or stored on the server.

Short follow-ups carry only whitelisted program IDs and an optional pending topic, not arbitrary conversation facts or instructions. Missing/ambiguous references prompt the student to choose a program. Full conversation history is not sent to the model; the resolved question and freshly retrieved records are its evidence. Refreshing or New chat resets the frontend context. This is lightweight lexical matching for the supplied FAQ collection, not a general natural-language understanding guarantee. Review and expand the regression questions as the document changes.

## API

- `GET /api/health`: process availability, record counts, mode and readiness; HTTP 200 does not imply content readiness.
- `GET /api/suggestions`: questions from verified records, grouped into the three design topics. Topic notes identify information absent from the document.
- `POST /api/chat`: JSON object with `message` (1–1,000 characters), optional `context`, and optional `mode: "faq"`. Success returns `success`, `reply`, `sources`, `details`, `warnings`, `context`, and `mode` where applicable. Invalid input/context returns 400, missing configuration 503, provider failure 502.

Private-record questions receive a privacy response, including common Tagalog and third-person variants. Unknown questions get a source-free fallback before any AI call. Messages, source quotes and warnings are rendered as text, never inserted as HTML. API keys stay on the backend. Requests have frontend and SDK timeouts; failed requests remain retryable.

Return the last response's `context` with a follow-up, for example `{"message":"And faculty?","context":{"programs":["bscs"]}}`. The server accepts at most three known program IDs and a small whitelisted pending topic; it rejects facts, roles and prompt instructions in context. To explicitly request a provider-free answer, include `"mode":"faq"`; the response is labeled FAQ mode. Errors with `can_use_faq: true` enable this recovery option. Retry uses the original message/context without creating duplicate user messages or discarding an unsent draft. Retrying an old turn does not overwrite the newer topic context.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

Linux: `.venv/bin/python -m pytest -q`. Optional browser checks use Playwright and Chromium: install Playwright separately (`python -m pip install playwright`, then `python -m playwright install chromium` if no Chromium is installed), start a separate test server in FAQ mode, and run `python tests/browser_smoke.py` followed by `python tests/browser_improvements.py`. These check six viewport sizes, source panels, real requests, follow-ups, reset, Retry/FAQ recovery, copying and safe text rendering. Simulated provider failures are explicitly identified in the results.

With that FAQ server running, `python tests/evaluate_questions.py` records actual HTTP replies in `docs/evaluation-improved.json`. The current regression run passes 230 automated tests, 20 browser scenarios and 95/95 expected source-support/mode checks. The 33 phrasing cases from the review improved from 8 expected-source matches to 33; this is the same regression set used during implementation, not an independent accuracy estimate. See [validation evidence](docs/testing.md) and [improvement notes](docs/improvements.md). Synthetic test records are never loaded by the application.

## Remaining work

Confirm source currency and missing office/admissions information with CCIT, review the recorded source-question evaluation, and verify live AI with valid credentials and available quota. No department-specific facts were invented or silently corrected in this update. Desktop, tablet and mobile Chromium checks and actual screenshots are complete; Safari, Firefox, real mobile devices and screen-reader behavior have not been tested. The supplied file contains no visible conversation/error/mobile frames; these states use the same design system. This is not a claim of an exact pixel match or independently verified answer accuracy. Gemini and OpenAI integrations have been tested with in-memory SDK transports, but successful live generation has not been confirmed here. Future improvements include wider held-out language evaluation, opt-in history, deployment rate limits and verified official contact links.
