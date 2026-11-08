# Dataset and data dictionary

## Source and active knowledge

`knowledge.json` contains **220 active FAQs** transcribed from the supplied `sources/database_v3.json` and department-chair update. Titles, alternative questions, answers, and keywords retain supplied wording. Source text is reference data, never application instructions.

Runtime IDs are `FAQ-001` through `FAQ-221`, excluding retired `FAQ-020`. Other IDs were not renumbered. The older overview and its examples were removed by user request; FAQ-189 retains the laboratory overview and FAQ-190 covers access. Raw source record 20 remains as provenance but is not active knowledge or a training label. The first twelve source IDs use a different ordering from the runtime IDs; `source_id` records that mapping.

Important knowledge fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable runtime FAQ ID |
| `category` | Runtime topic used in source selection |
| `question`, `alternative_questions` | Supplied canonical and alternative questions |
| `answer`, `keywords` | Supplied answer and matching terms |
| `source_id`, `source_category`, `source` | Link back to the supplied source record |
| `verification_status`, `verification_scope` | Source transcription was checked; this does not certify the institution's current policy |
| `reviewed_at`, `currency_status` | Transcription-review date and unconfirmed institutional currency |

The dated officer roster covers A.Y. 2025–2026. Department-chair entries name Judith G. Elic (BSIT), Dr. Farley L. Abrigo (BSCS), and John Benedict Palomeno (BSEMC). Current assignments, policies, and wider redistribution permission have not been independently confirmed. No license was supplied for the department data. Source extraction and AI authorship do not establish permission to publish it broadly.

## Classification questions

`questions.csv` has **1,825 labeled English questions** across all 220 active FAQs:

| Split | Count | Origin and use |
| --- | ---: | --- |
| train | 945 | Supplied titles/alternatives; fits vocabulary and feature counts |
| validation | 440 | Two AI-authored questions per label; selects among four fixed settings |
| test | 440 | Two different AI-authored questions per label; evaluates the selected setting |

These examples are constructed, not student transcripts or independent human annotations. They are sufficient to demonstrate the workflow but not to support population-level accuracy or usefulness claims. Related wording and shared templates can remain across splits.

`holdouts.json` stores the fixed validation/test questions. `tools/build_dataset.py` materializes the CSV and `dataset_audit.json` records source-question conflicts and the dataset fingerprint. Shared canonical titles take precedence over broader alternatives; unresolved label conflicts are excluded and documented. The CCIT Camp question belongs to FAQ-211 rather than the general activities entry FAQ-022.

The three chair labels received new holdouts before their expanded experiment. FAQ-020's six training/two validation/two test examples were subsequently removed with that class. All retained questions keep their wording and split. Recomputed scores on this revised corpus are not a new independent evaluation. Do not edit held-out questions or tune parameters to improve a score already inspected.

## CSV schema

| Field | Meaning | Model role |
| --- | --- | --- |
| `sample_id` | Unique example ID | Audit metadata |
| `question` | Nonempty text up to 1,000 characters | Only input feature source |
| `faq_id` | An active FAQ label | Prediction target |
| `split` | `train`, `validation`, or `test` | Partition control |
| `language` | Authoring-language tag | Description only; current corpus is English |
| `provenance` | Supplied/constructed origin | Audit metadata |

A training example uses a question such as `Who is the IT Department Chair?` with target `FAQ-219`, split `train`, and language `English`. Existing sample IDs retain their original version prefix for traceability.

The loader standardizes case, Unicode, apostrophes, and spaces. It counts missing/invalid rows and within-split duplicates; conflicting labels and cross-split duplicate questions stop processing. Valid long questions are described using the upper IQR fence and retained. FAQ IDs, answers, language tags, and split metadata do not enter the question features. Word order, negation, and program/course identifiers are retained where relevant.

## Reproduce and interpret

```bash
python tools/build_dataset.py
python analyze.py
```

The selected model is unigrams with alpha 0.5. Validation: **366/440 correct, macro F1 0.827**. Test: **353/440 correct (80.2%), macro F1 0.807**. All 87 test errors and every prediction are retained in `research/results/report.json` and `test_predictions.csv`. There are only two test questions per label; individual-topic conclusions are limited.

`research/results/` holds one current model, report, comparison/prediction/prepared-data CSVs, and five charts. Its metadata records knowledge and dataset SHA-256 fingerprints; Flask rejects a mismatched model. The current dataset SHA-256 is `29170367949dcd31b246ed506506728235b9510cca1312b372cac34bbcb512dc`.

The classifier ranks known labels, not factual truth. Chat applies source support and scope checks separately. Explicit short forms and bounded typo handling support quick typing; unknown codes, names, years, and unsupported details are not freely guessed. No private student records are required, and the server does not store chat transcripts. Optional provider wording sends selected source context externally; FAQ mode does not.
