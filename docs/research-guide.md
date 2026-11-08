# Course analysis and demonstration guide

CCIThink's topic was approved by the instructor, as confirmed by the user on November 8, 2026. This update adapts it to the uploaded **Final Project: AI-Powered Data Analysis and Prediction System** guidelines. The original chat UI, concise answers and bold facts are preserved. The additional task is supervised prediction of a question's FAQ ID, with a separate analysis page.

For learning the implementation before presenting, use the separate [beginner walkthrough](learning/README.md). It explains each file/function, a real question trace, Bayes arithmetic, a suggested seven-day practice/build sequence and defense questions. The backend now uses numbered stages and ordinary loops so the core request/training path can be read directly.

## First run in Windows / VS Code

From the repository folder in an activated virtual environment:

```powershell
git pull
py -m pip install -r requirements-research.txt
py analyze.py --dataset data/question_dataset.csv
py app.py
```

Open `http://127.0.0.1:5000/` for chat and `http://127.0.0.1:5000/analysis` for the course demonstration. Stop an existing Flask process with Ctrl+C before starting the updated version. Refresh the browser after updating.

The local classifier and analysis need **no API key**. FAQ replies require `CHAT_MODE=faq` in the ignored `.env`. Optional AI-generated answers still use `CHAT_MODE=ai` and the configured Gemini/OpenAI key. Install `requirements.txt` alone if you only need the app with the committed model and charts; the extra research dependencies are for regenerating analysis and documents.

On Linux, use `.venv/bin/python` in place of `py` after installing the optional research dependencies in that environment.

## Demonstrate the required workflow

1. Open `data/question_dataset.csv`. Explain its six fields and provenance using `data/README.md`.
2. Run `py analyze.py --dataset data/question_dataset.csv`. It loads a CSV, validates/normalizes text, describes cleaning and length outliers, trains four configurations on training rows, selects on validation macro F1 and evaluates only the selected model on the frozen test split.
3. Open `/analysis`. Show basic dataset information, cleaning counts and the first three EDA charts. Explain the balanced class counts, question lengths and approximate language tags.
4. Show the validation comparison and test confusion matrix. The measured result is **28/44 correct (63.6% accuracy), macro F1 0.595**, with a **2/44 majority baseline**. Discuss the sixteen errors and the small sample instead of claiming real-world accuracy.
5. Try `Who teaches BSCS?` in the local classifier. Explain its predicted FAQ label and uncalibrated relative score. Entering a question does not store it.
6. Return to chat. Ask a supported public question and an unsupported question such as `What time do the labs open?`. Explain how a classifier prediction cannot bypass source-support checks. A small bounded score bonus assists ranking.
7. Show the test commands and ethical limitations. Distinguish software regression checks from classifier hold-out evaluation and from a real student study.

## Import a different dataset

The command-line interface is the dataset-import interface; no web upload or public retraining endpoint is exposed. Supply a local UTF-8 CSV with the documented schema and labels mapped to the existing FAQ IDs:

```powershell
py analyze.py --dataset path/to/questions.csv --output-dir research/custom-run
```

Each included class needs train, validation and test rows. Blank/invalid rows and within-split duplicate questions are counted and removed. Unknown labels, conflicting labels, repeated sample IDs and cross-split duplicate questions stop the run. Numeric scores do not imply that new source facts have been verified. Do not import private student conversations without an appropriate, permissioned process.

The custom output directory keeps that experiment separate from the bundled application model. The app reads `research/results`; re-running the default experiment replaces those artifacts. Restart Flask after intentionally updating its model. A changed knowledge fingerprint invalidates stale model counts and preserves ordinary retrieval. Numerical analysis can run with `--no-figures` without Matplotlib.

## Files produced by the analysis

| Artifact | Contents |
| --- | --- |
| `research/results/report.json` | Dataset profile, cleaning counts, protocol, validation comparison, test metrics, confusion matrix, language breakdown, every error and limitations |
| `research/results/model.json` | Trained NB counts and training IDs, vocabulary, smoothing and source/dataset fingerprints; no executable model pickle |
| `research/results/prepared_dataset.csv` | Cleaned and normalized rows with original partition assignments |
| `research/results/experiments.csv` | Four validation-only configurations |
| `research/results/test_predictions.csv` | Every selected-model test prediction, label and relative score |
| `research/results/figures/` | Three EDA charts, validation comparison and test confusion matrix |

The corpus is AI-assisted and constructed. It has no exact train/validation/test duplicate overlap, and its validation/test questions have no exact normalized overlap with the older 95-question fixture. Related templates and common authorship still limit independence. Do not tune on the current test set after reading its errors; create fresh test evidence for the next development round.

## Papers and presentation

`docs/paper/` contains an IMRaD manuscript and a separate five-chapter technical report, each in editable DOCX, PDF and Markdown. The latter follows the professor's chapter order. The 12-slide defense deck is available as PPTX and PDF, with speaker notes in Markdown and in the PPTX. Suggested speaking time is 10–15 minutes followed by the required 5-minute Q&A.

Regenerate these files from measured results:

```powershell
py tools/build_project_documents.py
```

The three confirmed authors are **Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.** The files are drafts for their review. AI assistance is disclosed. No participant results, interviews, satisfaction percentages, actual student transcripts or successful live AI generation are invented. Check instructor-specific formatting/disclosure rules and source permissions before submitting.

## Validation commands

```powershell
py -m pytest -q
```

Optional browser checks require Playwright and Chromium installed separately. With a FAQ server running:

```powershell
py tests/browser_smoke.py
py tests/browser_improvements.py
py tests/browser_analysis.py
py tests/evaluate_questions.py
```

Latest executed evidence: **263 automated tests**, **26 browser scenarios**, **95/95 existing HTTP checks**, and the separate **44-question classifier test**. Browser and source-support checks do not measure current departmental accuracy or human usability.
