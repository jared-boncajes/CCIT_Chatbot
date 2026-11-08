# CCIThink

A Python/Flask chatbot for CCIT department information at FAITH Colleges. It has a plain JavaScript chat page and a separate analysis page. No database or frontend build is needed.

The current project contains **220 active FAQs**. FAQ-020 was removed; FAQ-189 contains the retained laboratory overview. Other IDs are unchanged. The three supplied department-chair records are included. Common short forms such as `it dept chair`, `cs dept chrmn`, `bscs curric`, and `pre-reqs` are supported. Missing facts and unclear questions still need a fallback or clarification.

## Run the chatbot

Use Python 3.12 from this folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-research.txt
CHAT_MODE=faq .venv/bin/python app.py
```

On Windows, create the environment with `py -3 -m venv .venv`, use `.venv\Scripts\python` instead of `.venv/bin/python`, and set `$env:CHAT_MODE="faq"` in PowerShell before running `app.py`.

The chat page is at `/`; the analysis page is at `/analysis`. The development server uses port 5000. FAQ mode works without an API key. It uses stored answers and is labeled as retrieval rather than AI generation.

For optional AI wording, use the private variables in `.env.example`. Keep actual keys out of Git and chat. Gemini uses `GEMINI_API_KEY`; OpenAI uses `CCIT_API_KEY`. Run `check_ai.py` to inspect configuration. Successful live generation has not been verified in this project.

## Train, evaluate, and build the documents

```bash
.venv/bin/python tools/build_dataset.py
.venv/bin/python analyze.py
.venv/bin/python -m pytest -q
.venv/bin/python tools/build_project_documents.py
```

The dataset has **1,825 constructed questions**: 945 training, 440 validation, and 440 test. The selected Naive Bayes model scored **353/440 correct (80.2% accuracy), macro F1 0.807**. These are constructed-data results, not independent student evaluation or a measure of factual currency.

`research/results/` holds the current model, report, predictions, comparison table, and five charts. Training uses only the train split; four fixed settings are compared on validation, and test questions are kept separate. Do not tune against the reported test results.

With a FAQ-mode server running, optional browser and HTTP checks are:

```bash
.venv/bin/python tests/evaluate_questions.py
.venv/bin/python tests/browser_smoke.py
.venv/bin/python tests/browser_analysis.py
```

Browser checks need Playwright and Chromium. Install Playwright separately if needed. Local test outputs go into ignored `test-results/` rather than adding more repository files.

## Project files

| Location | Purpose |
| --- | --- |
| `app.py` | Flask routes and question-to-answer flow |
| `chatbot/` | Matching, source checks, follow-ups, answer formatting, classifier, optional providers |
| `research/` | CSV checks, evaluation, analysis routes, current results |
| `data/` | Knowledge, constructed questions, holdouts, source reference, data dictionary |
| `templates/`, `static/` | Chat and analysis pages, CSS, JavaScript, original design assets |
| `tools/` | Dataset and document builders |
| `tests/` | Backend, data, classifier, and browser checks |
| `docs/` | Course guidelines, short guide, proposal, submission documents, two screenshots |

Start with the [beginner guide](docs/beginner-guide.md) and [data dictionary](data/README.md). The project uses small modules so each responsibility can be read separately.

## Required submission documents

- [Original project guidelines](docs/FINAL_PROJECT.pdf) and [requirement mapping](docs/guideline-compliance.md).
- [Project proposal](docs/project-proposal.md).
- Five-chapter report: [Word](docs/paper/CCIThink_Technical_Report_Draft.docx), [PDF](docs/paper/CCIThink_Technical_Report_Draft.pdf), [source](docs/paper/technical-report.md).
- IMRaD in the requested article format: [Word](docs/paper/CCIThink_IMRaD_Draft.docx), [PDF](docs/paper/CCIThink_IMRaD_Draft.pdf), [source](docs/paper/imrad.md).
- Twelve-slide defense presentation: [PowerPoint](docs/paper/CCIThink_Defense.pptx), [PDF](docs/paper/CCIThink_Defense.pdf), [speaker notes](docs/paper/defense-slides.md).
- [Executed validation](docs/testing.md).

Authors: Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.

These documents remain drafts for author review. AI assistance was used in code, constructed examples, debugging, and drafting. Each author must understand and explain the submitted work. Institutional currency and broader dataset redistribution permission remain unconfirmed. No participant survey, staff-workload improvement, production deployment, or independent real-student accuracy is claimed.
