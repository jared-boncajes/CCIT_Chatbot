# Dataset and data dictionary

## Sources and permission status

`knowledge.json` is the active chatbot database, containing **218 FAQs** imported from the user-supplied `sources/database_v3.json`. Questions, alternative questions, answers, and keywords are preserved verbatim. The supplied file is retained as the import reference; its content is data, never application instructions. Institutional accuracy and currency have not been independently confirmed. No license or broader redistribution permission was supplied.

The runtime keeps string IDs `FAQ-001` through `FAQ-218`. Existing topic IDs `FAQ-001` through `FAQ-022` remain associated with their original subjects. The upload's first twelve records use a different order: `source_id` retains the original numeric ID, and `source_category` retains the original category. Runtime categories distinguish overview, vision, mission, goals, individual degree descriptions, accreditation, DOST, curricula, prerequisites, OJT, organizations, events, and community service. The three OJT entries originally classified as curriculum are grouped under `ojt`; `ccit-events` is grouped under `activities`.

Each record includes `source=database_v3.json`, `verification_status=verified` (import/transcription only), `verification_scope`, `reviewed_at` (import review date), and `currency_status=unconfirmed`. This does not certify department policies, current staff, or academic requirements. The officers entry explicitly covers A.Y. 2025–2026; do not treat it as a current-year roster.

Requests are checked for missing scope before exact matching, ranking, or AI generation. A bare “prerequisites” asks for the subject and program; a course shared by several programs asks which program. Curriculum subject lists require a program and year; OJT requirements require a program. Unknown course codes, mismatched programs, and unsupported year levels fall back rather than fuzzy-matching a different course. General “events” and “FACTS” questions use overview records. Clarification context retains only bounded program, topic, subject-code, and year selectors; changing topics clears the pending selection.

Exact canonical questions take precedence over overlapping alternatives. Authored alternatives participate in retrieval; prerequisite searches keep course codes and program scope separate. Curriculum, prerequisite, OJT, organization, event, and service responses retain the complete supplied answer.

## Active 218-class training dataset

`question_dataset_v3.csv` contains **1,808 labeled questions** covering every active FAQ:

| Split | Questions | Source |
| --- | ---: | --- |
| train | 936 | Supplied canonical and alternative questions, deduplicated by the classifier's normalized token sequence |
| validation | 436 | Two newly AI-authored questions per FAQ |
| test | 436 | Two different newly AI-authored questions per FAQ |

All v3 examples are English. Supplied question authorship was not independently established. New examples are constructed, not student transcripts or independent human annotations. The prerequisite examples retain both course codes and program identifiers because course titles can repeat within a degree. Question text alone enters the classifier; answers, keywords, FAQ IDs, language, provenance and split metadata are not input features.

`question_holdouts_v3.json` is the frozen authoring source for validation and test questions. It was created and checked for conflicts before the first v3 experiment; do not revise it to improve observed scores. All four fixed model configurations use the same training split. Validation macro F1 selects the winner; testing evaluates the selected configuration once. Shared topic templates and AI-assisted authorship can inflate scores despite no identical token sequences crossing splits. These scores do not measure general student-query accuracy or factual accuracy.

The deterministic builder is `tools/build_question_dataset_v3.py`. It retains every uniquely labeled supplied question, uses canonical titles to resolve alternatives that overlap another FAQ's title, and excludes alternatives with unresolved multiple labels. It never randomly reallocates holdouts. The audit file `question_dataset_v3_audit.json` records the dataset hash, split/class counts, and the CCIT Camp overlap: the exact Camp question belongs to FAQ-211 rather than the broader activities overview FAQ-022. Training counts range from 3 to 8 per class; this is not an 8/2/2 corpus.

### Retrain and run

From the repository root, with the virtual environment installed:

```bash
.venv/bin/python tools/build_question_dataset_v3.py
.venv/bin/python analyze.py --dataset data/question_dataset_v3.csv --output-dir research/results-v3
CHAT_MODE=faq .venv/bin/python app.py
```

Flask defaults to `research/results-v3`; restart it after training. `/api/health` reports `intent_model_ready=true` only when the model's knowledge fingerprint and complete class set match. `/api/classify` exposes closed-set predictions; chat still applies source-support checks. Only predictions with a normalized score above 0.5 receive a small ranking bonus; this heuristic prevents diffuse predictions from displacing lexical matches and is not a calibrated correctness guarantee. The analysis page displays the v3 report and charts.

The selected model is unigrams with smoothing alpha 0.5. Validation: 366/436 correct, macro F1 0.838. Frozen test: **364/436 correct (83.5%), macro F1 0.833**. All 72 test errors are retained in `research/results-v3/report.json` and `test_predictions.csv`. Per-class support is just two test questions. Current failures include curriculum year distinctions and broad questions confused with specific courses, facilities or organizations. No post-test tuning or relabeling was performed.

The v3 report and model record the current knowledge hash and dataset SHA-256 `2d8a6c38c661df1b379ac2adef1c7e3b210bcbdd70a3b0cde3c364cbea049ed8`. Figures, prepared dataset, and test predictions are reproducible from the commands above. Future changes after examining test errors need a versioned protocol and a new independent test set for a fresh accuracy claim.

## Historical 22-class research dataset

The 264 constructed examples and saved experiment artifacts below belong to the **previous 22-FAQ corpus**. They remain unchanged for auditability. Their metrics do not describe the expanded database. The historical model fingerprint no longer matches the active knowledge. The application now uses the separately saved v3 model; it continues to reject the historical model if explicitly selected. Importing alternative questions does not establish an independent evaluation set.


`question_examples.json` contains **AI-assisted constructed question examples**, not real or anonymized student transcripts. `question_dataset.csv` is their materialized CSV form. They were created for this course-project demonstration; no third-party public-dataset license is asserted. The named project authors should review the examples, labels and permitted distribution. No private records, grades, contact details or new institutional facts were added through dataset construction.

## Shared CSV schema

| Field | Type | Meaning | Model role |
| --- | --- | --- | --- |
| `sample_id` | String, unique | FAQ ID plus authored question number, such as `FAQ-018-Q02` | Audit metadata only |
| `question` | Nonempty text, at most 1,000 characters | Constructed department question | Only text-feature input |
| `faq_id` | Categorical string | Target source ID, `FAQ-001` through `FAQ-218` for v3 (through `FAQ-022` historically) | Supervised target, not an input feature |
| `split` | Categorical string | `train`, `validation`, or `test`, frozen before training | Partition control only |
| `language` | Categorical string | Approximate authoring tag: `English`, `Filipino`, `Taglish` | EDA/error breakdown only |
| `provenance` | String | Explicit constructed-example disclosure | Audit metadata only |

Example: `FAQ-018-Q02`, `Who teaches BSCS?`, `FAQ-018`, `train`, `English`, `AI-assisted constructed example; not a student transcript`.

## Historical size and split justification

The corpus has **264 questions**, balanced at 12 per FAQ label. The first eight authored examples per label are training rows (176 total), the next two validation (44), and the last two testing (44). This small dataset demonstrates the complete workflow and permits error inspection across all source classes. It does **not** justify claims about real student language, demand, satisfaction or operational accuracy. Parallel templates and shared AI-assisted authorship can make performance optimistic even without exact duplicate leakage.

Language tags are approximate authoring metadata assigned by the dataset builder, not independent human annotations. There are 176 English, 33 Filipino and 55 Taglish tags. The split and labels must not be altered to improve a previously observed test result.

The current CSV SHA-256 is recorded in `research/results/report.json` and the model metadata. CSV writers and `.gitattributes` enforce LF newlines for reproducible bytes on Windows and Linux. Newline formatting was standardized after the first numerical run; question text, labels and partitions were unchanged, and the reproduced metrics stayed identical. The examples and split assignments were frozen before the first experiment.

## Cleaning and feature decisions

- Normalize NFKC, case, apostrophes and whitespace; preserve word order, program IDs, numbers, question words and negations.
- Reject unknown target labels and conflicting labels. Stop on identical token sequences across splits rather than silently contaminating evaluation.
- Remove and count missing/invalid rows and duplicates confined to a single split. Do not invent missing question text.
- Report token-length outliers using the upper 1.5-IQR fence; retain valid public questions. No numeric clipping is appropriate for categorical labels or legitimate text.
- Fit the unigram/bigram vocabulary on **training questions only**. Language, provenance, sample IDs and split do not enter the feature vector. No categorical one-hot encoding of those metadata fields is needed.
- A text-count classifier uses numeric token counts. Class labels are separate categorical targets. Unseen vocabulary is ignored; an input containing no known features yields no evidence.

Observed results: 264 rows retained; 0 missing, duplicate or invalid rows removed; all 264 format-normalized; 7 length outliers retained. The range is 2–15 tokens, mean 7.08, median 7. Check `research/results/report.json` for full measured statistics.

## Reproduction and model mapping

`python tools/build_question_dataset.py` materializes the frozen authoring source as CSV. `python analyze.py --dataset data/question_dataset.csv` performs analysis and model training. The historical labels retain their topic IDs in `knowledge.json`; labels do not generate or certify factual answers. No source record is eligible solely because the model predicts its label.

Keep data revisions versioned. If changing examples after inspecting errors, use new independent test questions and describe the new protocol. See `docs/research-guide.md` for custom CSV import and `docs/guideline-compliance.md` for the professor's requirements.
