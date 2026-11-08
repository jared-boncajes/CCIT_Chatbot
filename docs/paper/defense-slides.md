## Slide 1: CCIThink

- CCIT information chatbot and explainable FAQ classifier
- Boncajes, Rhian Jared D.
- Marcos, Maricar N.
- Carandang, Jamie Pearl U.
- Principles of Artificial Intelligence and Data Science

**Speaker notes:** Introduce the team and approved department-information topic. This is a class prototype, not a student-record system. About 45 seconds.

## Slide 2: Problem and objectives

- Find supported answers within 220 active department FAQs.
- Prepare data, describe patterns, train a classifier, and evaluate results.
- Keep unclear and unsupported questions separate from supported answers.

**Speaker notes:** Explain the information-search problem without claiming measured waiting times or staff workload savings. About 1 minute.

## Slide 3: Dataset and source

- 1,825 labeled English questions; 220 FAQ labels.
- 945 train / 440 validation / 440 test.
- Training titles and variants were supplied with the knowledge.
- Holdouts are AI-authored constructed examples, not student transcripts.

**Speaker notes:** Show data/questions.csv and data/README.md. Explain why a small constructed corpus demonstrates the workflow but cannot establish population accuracy. About 1 minute.

## Slide 4: Cleaning and exploration

- Check missing fields, duplicates, labels, and formats.
- Reject label conflicts and cross-split duplicates.
- 0 missing, 0 duplicate, 0 invalid rows removed.
- Mean 12.33 tokens; 9 long valid questions retained.

**Speaker notes:** Explain that valid long questions remain. Only question text becomes input features. The reported cleaning counts are measured, not fabricated dirty data. About 1 minute.

## Slide 5: Coverage and bias

- All current dataset examples are English.
- The model test does not establish Filipino or Taglish accuracy.
- Topic counts are designed examples, not measured student demand.

**Speaker notes:** This is the third EDA visualization. Explain language coverage and the difference between dataset composition and real student behavior. About 45 seconds.

## Slide 6: How Naive Bayes works

- Count words in training questions for each FAQ label.
- Estimate a label prior and smoothed word likelihoods.
- Add log likelihoods to rank possible labels.
- Independence is an approximation; scores are uncalibrated.

**Speaker notes:** Open chatbot/intent_model.py and explain the worked example in docs/beginner-guide.md. The implementation uses ordinary Python, counters, loops, and math. About 90 seconds.

## Slide 7: Parameter experiment

- Compare four fixed unigram/bigram and alpha settings.
- Select with validation macro F1; keep test questions separate.
- Selected: Unigrams / a=0.5.
- Validation: 366/440 correct; macro F1 0.827.

**Speaker notes:** Explain the validation comparison and tie-breaking rule. No test-based parameter tuning or retraining on held-out questions. About 1 minute.

## Slide 8: Test results

- 353/440 correct (80.2%).
- Macro F1 0.807.
- Majority baseline: 0.5% accuracy.
- 87 errors; two test questions per label.

**Speaker notes:** Interpret actual and predicted labels. These are constructed-question classifier results, not chat-user satisfaction or independent real-world accuracy. About 1 minute.

## Slide 9: Errors and limitations

- Similar course and curriculum wording can confuse labels.
- AI-authored questions may share templates.
- FAQ-020 was retired by user request; other IDs remain stable.
- Recomputed results do not constitute a new independent study.

**Speaker notes:** Show an actual error in research/results/test_predictions.csv. Explain that changing the corpus changes the scores and does not itself prove better generalization. About 1 minute.

## Slide 10: Working demonstration

- Run python analyze.py, then start python app.py in FAQ mode.
- Use /analysis for five charts, metrics, and a local prediction.
- Use chat for source-supported answers and short forms.
- Try an ambiguous question and an unsupported detail.

**Speaker notes:** Demonstrate Who teaches BSCS?, it dept chair, and a missing contact detail. Distinguish application regressions from classifier test accuracy. About 90 seconds.

## Slide 11: Ethics and responsible AI

- No private student records are required.
- Source currency and permissions still need review.
- AI assistance is disclosed; authors must explain their work.
- Optional provider wording is not a verified live-generation result.

**Speaker notes:** Discuss privacy, source currency, language bias, and required AI disclosure. Optional AI mode sends selected context to a provider; FAQ mode does not. About 1 minute.

## Slide 12: Conclusion and next steps

- A complete data-science workflow supports the chatbot.
- The classifier remains limited to a constructed, closed-set task.
- Next: confirmed sources, permissioned student questions, independent labels.
- Questions and defense discussion

**Speaker notes:** Summarize the objectives and limitations. Prepare each team member to explain their contribution and the algorithm. Reserve 5 minutes for questions after the 10–15-minute presentation.
