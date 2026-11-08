# Course requirement mapping

The original, unmodified handout is [FINAL_PROJECT.pdf](FINAL_PROJECT.pdf), *Final Project: AI-Powered Data Analysis and Prediction System*. It is retained in the repository. This mapping describes implemented capabilities and submission drafts; it is not instructor approval or a grading claim.

| Handout requirement | Current implementation or deliverable |
| --- | --- |
| Real-world problem and proposal | `project-proposal.md`: department information access and question-to-FAQ classification. |
| Dataset loading and basic information | `data/questions.csv`, `research/dataset.py`, `analyze.py`, and `/analysis`. |
| Dataset source, features, size justification, permissions | `data/README.md`: 220 FAQs, 1,825 supplied/constructed examples, documented fields, small-demo limits, source permission/currency status. |
| Missing values, duplicates, formats, outliers, categorical features | CSV validation and measured cleaning counts; conflicting labels/cross-split duplicates rejected; valid length outliers retained; text counts are features and FAQ IDs are targets. |
| Descriptive statistics and at least three useful visualizations | Five saved charts: class counts, question lengths, language coverage, validation comparison, and test confusion matrix. |
| Implement and explain at least one algorithm | Standard-Python multinomial Naive Bayes in `chatbot/intent_model.py`; calculation and worked example in `beginner-guide.md` and Chapter 3. |
| Appropriate train/test separation | 945 train / 440 validation / 440 test; vocabulary and counts fit on training only; retained holdout wording/splits unchanged. |
| Meaningful comparison or parameter experiment | Four fixed unigram/bigram and alpha settings selected on validation macro F1; test compared with a training-majority baseline. |
| Appropriate metrics and interpretation | `research/results/report.json`, prediction/experiment CSVs, `/analysis`, and Chapter 4. Current test result: 353/440 (80.2%), macro F1 0.807. |
| Working demonstration and organized code | Flask chat, `/analysis`, and `/api/classify`; setup in README and a short file-reading guide. |
| Privacy, bias, reliability, responsible use | Reports and beginner guide discuss constructed data, English-only model evaluation, source currency/permissions, sparse classes, external providers, and limits. |
| Required Chapters 1–5 | `paper/CCIThink_Technical_Report_Draft.docx`, PDF, and `technical-report.md`: introduction, related systems/concepts, methodology, results/discussion, conclusions/recommendations. |
| APA 7 citations and references where applicable | Technical report uses author-date citations, reference titles, and hanging-indent references. Source/course handouts with no supplied author/date are identified honestly. Authors must review final citation details before submission. |
| Required appendices | Repository link, dataset sample/dictionary, two screenshots, test-case/evidence locations, user guide, and additional table/graph locations in the technical report. |
| Presentation and defense | `paper/CCIThink_Defense.pptx`, PDF, and speaker notes; 12 slides targeting 10–15 minutes plus 5-minute Q&A. |
| Requested IMRaD article format | Separate current IMRaD Word/PDF/Markdown with centered title/abstract and two-column Roman-numbered article sections. |
| Understand code; disclose assistance; do not fabricate findings | AI assistance is disclosed. A beginner guide and worked model calculation support explanation; each author must study and demonstrate their understanding. No participant, satisfaction, workload, or successful live-generation result is invented. |

All current report and slide metrics are generated from the same `research/results/report.json`. FAQ-020 was removed at the user's request; current labels, suggestions, and predictions exclude it. Source transcription is checked separately from institutional verification. Collecting independent student examples, permission review, and author/instructor review remain necessary before broader claims or final submission.
