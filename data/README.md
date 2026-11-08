# Dataset and data dictionary

## Sources and permission status

`knowledge.json` contains 22 FAQs extracted from the user-supplied **About CCIT.pdf**. Their `verification_status` records transcription checks, while `currency_status=unconfirmed` records that current institutional facts were not independently confirmed. No open license or broader redistribution permission was provided for that source. The original source PDF is not republished by this update. Confirm appropriate permissions and current facts with the department before broader release.

`question_examples.json` contains **AI-assisted constructed question examples**, not real or anonymized student transcripts. `question_dataset.csv` is their materialized CSV form. They were created for this course-project demonstration; no third-party public-dataset license is asserted. The named project authors should review the examples, labels and permitted distribution. No private records, grades, contact details or new institutional facts were added through dataset construction.

## CSV schema

| Field | Type | Meaning | Model role |
| --- | --- | --- | --- |
| `sample_id` | String, unique | FAQ ID plus authored question number, such as `FAQ-018-Q02` | Audit metadata only |
| `question` | Nonempty text, at most 1,000 characters | Constructed department question | Only text-feature input |
| `faq_id` | Categorical string | Target source ID, `FAQ-001` through `FAQ-022` | Supervised target, not an input feature |
| `split` | Categorical string | `train`, `validation`, or `test`, frozen before training | Partition control only |
| `language` | Categorical string | Approximate authoring tag: `English`, `Filipino`, `Taglish` | EDA/error breakdown only |
| `provenance` | String | Explicit constructed-example disclosure | Audit metadata only |

Example: `FAQ-018-Q02`, `Who teaches BSCS?`, `FAQ-018`, `train`, `English`, `AI-assisted constructed example; not a student transcript`.

## Size and split justification

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

`python tools/build_question_dataset.py` materializes the frozen authoring source as CSV. `python analyze.py --dataset data/question_dataset.csv` performs analysis and model training. Each label maps directly to the matching `id` in `knowledge.json`; labels do not generate or certify factual answers. No source record is eligible solely because the model predicts its label.

Keep data revisions versioned. If changing examples after inspecting errors, use new independent test questions and describe the new protocol. See `docs/research-guide.md` for custom CSV import and `docs/guideline-compliance.md` for the professor's requirements.
