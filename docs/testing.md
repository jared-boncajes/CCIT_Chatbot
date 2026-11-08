# Validation evidence

The latest automated run completed with **263 passed** (`.venv/bin/python -m pytest -q`). It covers the original 94 checks, 146 chat regression checks and 23 research checks. These cover reviewed question variants, English/Tagalog phrasing, unsupported facts, direct bold summaries, source metadata, context, explicit FAQ override, privacy/recovery, hand-calculated Bayes scores, bigram order, data cleaning/leakage rejection, stale/invalid models, reproducible experiment outputs and the analysis/prediction endpoints. No test uses a real AI credential.

## Separate classifier evaluation

`python analyze.py` loads 264 AI-assisted constructed questions (176 training, 44 validation, 44 testing). Four prespecified unigram/bigram and smoothing configurations were selected using validation macro F1. The selected unigram-plus-bigram model, alpha 0.5, scored **28/44 correct (63.6% accuracy), macro precision 0.629, macro recall 0.636 and macro F1 0.595** on the frozen test partition. The training-majority baseline scored **2/44 (4.5%), macro F1 0.004**. See `research/results/report.json`, `experiments.csv`, `test_predictions.csv` and figures for the actual results and all sixteen errors.

No vocabulary/counts were fitted on validation or test examples. Exact cross-split duplicate questions stop the run. Related templates and AI-assisted authorship remain limitations, and there are only two test questions per class. Validation/test examples have no exact normalized overlap with the older 95-question fixture. No real-student accuracy claim or human study is established. Approximate language tags are authoring metadata, not independently annotated gold labels.

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

`python tests/browser_analysis.py` passed **6 more scenarios**, bringing the browser total to **26**. These verify measured metrics and five loaded figures; mobile layout and actual local predictions; unseen-vocabulary abstention; rejection of private-record requests; simulated failure followed by real recovery; and safe literal prediction text plus return to the preserved chat UI. Reports/screenshots are in screenshots/analysis/. The chat homepage template, original CSS and original JavaScript were not changed by the research update.

## Document artifacts

`python tools/build_project_documents.py` generated the IMRaD manuscript and five-chapter technical report in DOCX/PDF/Markdown, plus a 12-slide PPTX/PDF deck with speaker notes. Both papers use the confirmed author names and the actual retained result artifacts. PDF pages were rendered and inspected, including the title/abstract, charts, tables, references and a results slide; embedded fonts avoid viewer substitution. DOCX and PPTX structures were opened with their Python libraries. No fabricated participant or satisfaction results are included.

The readability refactor expands the main routes, word scoring, Naive Bayes calculation, dataset checks and metric counts into explicit steps/loops. The existing regression and numerical-reproduction checks still pass, with unchanged model settings and published results. `tools/build_walkthrough.py` exports a separate beginner guide in Word/PDF/Markdown, including a current function index, every included file and a suggested seven-day learning/build plan.

## Provider and diagnostic coverage

SDK tests use real SDK serialization/parsing with in-memory HTTP transports. They exercise Gemini/OpenAI grounding payloads, default models/key selection, source-only replies, empty/blocked results, quotas without retries, safe classification/logging of 400/403/404/429/503 and connection/timeout errors, model listing and secret-free CLI output. Model-finder tests cover the three-request cap, early success, exclusion of media/preview/Pro IDs, immediate stop on quota/access/connection errors and preservation of .env.

No successful live generation has been confirmed here. The user separately reported a live 503 for gemini-3.8-flash and 404 for the listed gemini-2.5-flash-lite. The model finder remains available to test actual per-project generation access locally.

## Limits

Source transcription is checked against the supplied PDF; current department facts remain unconfirmed. Firefox, Safari, actual mobile devices, screen readers, deployment/load testing and broad independently collected language evaluation remain unrun. JavaScript syntax and Git whitespace checks passed. Runtime dependencies remain unchanged; optional chart/document-generation dependencies are pinned in requirements-research.txt.

## Department-chair and shorthand update (2026-11-08)

The expanded knowledge base has 221 records, including the three user-supplied department chairs. Validation of this update passed 832 pytest cases, including a texting-form variant of every canonical FAQ, 726 supplied alternative questions, chair identity/scope checks, privacy wording, and unsupported-detail guards. The original 218 source records and their frozen validation/test questions were checked for preservation.

A fresh FAQ-mode server passed all 95 existing HTTP source-support checks, 14 chat browser checks across six viewport sizes, and 6 analysis browser scenarios. Additional Chromium requests confirmed that `it dept chair` and `cs dept chrmn` display the supplied names. The browser scripts now use current suggestions and report-driven analysis metrics instead of historical dataset constants. Simulated failure scenarios remain identified in their runner output.

The retrained classifier used 951 training, 442 validation, and 442 test examples. Test performance was 365/442 (82.6%), macro F1 0.822. These constructed-data scores are separate from application regression results. The original holdouts were retained; the three new labels received AI-authored holdouts before the expanded experiment. This is not independent student validation.

The IMRaD Word file was checked for its two-column section and Roman-numbered headings. The generated five-page PDF was rendered for visual inspection of its first and final pages; title, abstract, columns, references, and current metrics were checked. The layout follows the supplied Klarify example while preserving CCIThink authorship and measured findings. Reproduction: `python tools/build_imrad.py`.
