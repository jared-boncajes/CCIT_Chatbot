## Slide 1: CCIThink

- CCIT information chatbot + explainable FAQ classification
- Boncajes, Rhian Jared D.
- Marcos, Maricar N.
- Carandang, Jamie Pearl U.
- Principles of Artificial Intelligence and Data Science · November 2026

**Speaker notes:** Introduce the approved topic and team. Explain that this is a small educational prototype, not a student-record or grade-prediction system. About 45 seconds.

## Slide 2: Problem and objectives

- Find answers within 22 documented department FAQs.
- Preserve the existing chat UI and source-support checks.
- Demonstrate data preparation, learning, evaluation and interpretation.

**Speaker notes:** Frame information access as the project problem. Do not claim measured workload reduction or student satisfaction. About 1 minute.

## Slide 3: Dataset and provenance

- 264 AI-assisted constructed questions; 22 FAQ target labels.
- 176 training / 44 validation / 44 test; fixed assignments.
- Not real student conversations; no private records.
- Eight training, two validation and two test questions per label.

**Speaker notes:** Show question_dataset.csv and the data dictionary. Explain why a small corpus can demonstrate the workflow but cannot establish real-world effectiveness. About 1 minute.

## Slide 4: Preprocessing and EDA

- Validate schema, label IDs, split membership and input limits.
- Reject label conflicts and cross-split duplicates.
- 264 normalized; 0 missing, duplicate or invalid rows removed.
- Mean length 7.08 tokens; 7 longer valid questions retained.

**Speaker notes:** Demonstrate actual cleaning statistics, not synthetic claims of dirty real data. Explain why outlier lengths were retained and why labels/language metadata are not features. About 1 minute.

## Slide 5: Language coverage

- 176 English / 33 Filipino / 55 Taglish authoring tags.
- Tags are approximate, not independently annotated.
- The corpus is balanced by FAQ, not sampled from student demand.

**Speaker notes:** This is the third EDA visualization. Discuss representativeness and language bias, and distinguish designed counts from observed real student behavior. About 45 seconds.

## Slide 6: Implemented algorithm

- Multinomial Naive Bayes, implemented in standard Python.
- Count unigrams or unigrams plus adjacent bigrams.
- Learn vocabulary and class-feature counts on training data only.
- Additive smoothing avoids zero likelihoods; scores are uncalibrated.

**Speaker notes:** Open chatbot/intent_model.py. Explain the log-prior plus feature-count-weighted log-likelihood equation. State the conditional-independence assumption and why it is imperfect for language. About 90 seconds.

## Slide 7: Validation experiment

- Four fixed feature/smoothing configurations.
- Choose using validation macro F1, not test accuracy.
- Selected: unigrams + bigrams, alpha = 0.5.
- Validation: 31/44 correct; macro F1 = 0.663.

**Speaker notes:** Explain each axis and the tie-breaking rule. Training and validation remain separate; the selected model was not refitted on validation data. About 1 minute.

## Slide 8: Frozen-test results

- 28/44 correct: 63.6% accuracy.
- Macro F1 = 0.595; macro precision = 0.629.
- Majority-class baseline: 2/44 correct (4.5%).
- 16 mistakes; only two test questions per label.

**Speaker notes:** Interpret the confusion matrix and the limits of the baseline. Do not call the classifier perfect or generalize its percentage to all users. About 1 minute.

## Slide 9: Error analysis

- English-tagged test: 16/22 correct.
- Filipino-tagged test: 3/8; Taglish: 9/14.
- Overview, offerings and IT/CS definitions were difficult.
- Small constructed groups do not establish population differences.

**Speaker notes:** Open test_predictions.csv and show an actual mistake. Explain sparse wording and overlapping intents as plausible, untested explanations. About 1 minute.

## Slide 10: Working demonstration

- Run python analyze.py, then python app.py.
- Use /analysis for charts, cleaning, metrics and predictions.
- Use / for the preserved chat interface and short bold answers.
- ML only adds a bounded ranking bonus after source checks.
- 263 automated tests; 26 browser scenarios; 95/95 chat checks.

**Speaker notes:** Demonstrate Who teaches BSCS? on the analysis page and the chat. Then show an unsupported detail falling back. Explain that the 95 checks are regression tests, not classifier hold-out accuracy. About 90 seconds.

## Slide 11: Ethics and limitations

- No private student records; no stored chat transcript.
- Department facts and source permissions still need appropriate review.
- AI assistance is disclosed; every author must understand the code.
- No participant study, production-load result or successful live LLM claim.

**Speaker notes:** Discuss language bias, source currency and provider privacy. Note that optional AI answer mode sends selected information to the chosen provider. About 1 minute.

## Slide 12: Conclusion and next steps

- A reproducible AI/Data Science workflow now supports the chatbot.
- The classifier outperformed a weak baseline but needs improvement.
- Next: confirmed facts, permissioned student examples, independent labels and a fresh test set.
- Questions and defense discussion

**Speaker notes:** Answer the three research questions briefly. Reserve the professor-required 5 minutes after the 10–15 minute presentation for questions. Do not claim field effectiveness. About 45 seconds.
