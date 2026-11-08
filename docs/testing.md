# Executed validation

The current project has 220 active FAQs; FAQ-020 is retired and the other IDs remain stable. Checks were run after consolidating the project into one dataset and one result folder.

| Check | Outcome |
| --- | --- |
| Python regression suite | 832 passed; no skipped tests reported |
| HTTP source-support checks | 95/95 passed against a fresh FAQ-mode server |
| Chat browser checks | 14 passed, including six viewport sizes, real replies, personalization, reset, privacy/fallback, safe text, and simulated failure recovery |
| Analysis browser checks | 6 passed, including current metrics/charts, local prediction, unknown vocabulary, privacy, simulated failure, and recovery |
| Dataset/model reproduction | CSV builder preserves fixed bytes; training reproduces the recorded model comparison and test scores; holdout-only words do not enter the trained vocabulary |
| Retired FAQ checks | No active record, dataset label, model class, analysis label, suggestion, or returned source uses FAQ-020; laboratory questions use FAQ-189 |
| Required documents | Original guideline PDF is byte-identical to the upload; report has Chapters 1–5, references, appendices, current metrics; deck has 12 slides; IMRaD retains the requested article format |
| Document review | PDF report and results slide rendered for visual inspection; Word/PPTX opened with their Python libraries; local Markdown links checked |

## Reproduce

```bash
python tools/build_dataset.py
python analyze.py
python -m pytest -q
python tools/build_project_documents.py
```

With the FAQ-mode server running:

```bash
python tests/evaluate_questions.py
python tests/browser_smoke.py
python tests/browser_analysis.py
```

Browser checks use Playwright and Chromium. Their result files and optional screenshots go to ignored `test-results/`. Two current screenshots needed for the report appendix remain in `docs/screenshots/`.

## Measured classifier results and limits

The current corpus has 1,825 questions: 945 train, 440 validation, 440 test. The selected unigrams/alpha-0.5 model scores 366/440 correct on validation (macro F1 0.827) and 353/440 on test (80.2%, macro F1 0.807). All 87 test mistakes remain in the current prediction CSV and report.

Those constructed-data results differ from source-support regression checks. The retained holdouts keep their wording and split; removing an FAQ changes the corpus and does not create an independent new evaluation. No real-user satisfaction, workload reduction, production-load measurement, or successful live provider generation has been established. Department currency, source permissions, independent student questions, author understanding, and final instructor review remain outside what passing software checks can certify.
