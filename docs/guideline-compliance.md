# Professor guideline mapping

Source: uploaded **FINAL PROJECT.docx.pdf**, titled *Final Project: AI-Powered Data Analysis and Prediction System* (15 pages). This checklist treats the handout as course requirements. It does not change the user's instruction to preserve the chatbot UI or claim instructor grading/acceptance.

**Topic approval:** the user confirmed on November 8, 2026 that the CCIT chatbot topic was approved. **Authors:** Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.

| Guideline | Implementation / evidence |
| --- | --- |
| Relevant real-world problem | Department information access; learned task is question-to-FAQ classification. No claim that administrative workload or satisfaction was measured. |
| Dataset loading and basic information | `analyze.py --dataset <CSV>`; `data/question_dataset.csv`, data dictionary and `/analysis` dataset/cleaning summary. |
| Dataset source and sufficiency | 22 supplied FAQs and 264 explicitly constructed questions. Size justified for a controlled demonstration; insufficient for population claims. |
| Missing values, duplicates, inconsistent formats | `research/dataset.py` validates schema/values, normalizes text, counts removed rows and stops on conflicting labels/cross-split leakage. Actual zero removals are reported honestly. |
| Outliers and categorical features | Length IQR outliers are described and retained when valid. FAQ IDs are targets; metadata is excluded; text becomes numeric counts. |
| Descriptive statistics and at least three useful visualizations | Class distribution, token-length histogram and approximate language distribution. Additional validation comparison and test confusion matrix. |
| At least one implemented AI/ML algorithm | Standard-Python multinomial Naive Bayes in `chatbot/intent_model.py`; trained from the project's CSV, not a prebuilt-model-only demonstration. |
| Explain algorithm operation and limitations | Equation, priors, likelihoods, smoothing, n-grams, assumptions and uncalibrated scores explained in both papers and defense notes. |
| Appropriate train/test separation | Fixed 176 training / 44 validation / 44 test questions. Vocabulary/counts fit on training only; selection uses validation. Exact cross-split duplicates stop the run. |
| Meaningful comparison / parameter experiment | Four prespecified unigram/bigram and alpha combinations; validation macro F1 selects. Selected-model test compared with training-majority baseline. |
| Task-specific evaluation | Accuracy, macro precision/recall/F1, all per-class metrics, confusion matrix, language breakdown and every observed test error. |
| Results and interpretation | Read-only `/analysis`, exported JSON/CSV/figures and written results/discussion; measured 28/44 correct, macro F1 0.595. |
| Working demonstration | Original chat plus separate `/analysis` and `/api/classify`; training/import via local CLI. No public retraining endpoint. |
| Privacy, bias, reliability and appropriate use | Ethics sections cover constructed data, language imbalance, small test size, source currency, external-provider use and source permission status. |
| Project proposal | `docs/project-proposal.md`. |
| Runnable, organized source | `app.py`, `chatbot/`, `research/`, `analyze.py`, pinned runtime and optional research dependencies; setup in README and research guide. |
| Students understand and explain submitted code | The separate Word/PDF beginner walkthrough explains every included file, runtime/data flow, model arithmetic, tests and defense questions. Backend logic uses explicit loops and numbered steps; authors still need to study and demonstrate understanding themselves. |
| Required five-chapter documentation | `docs/paper/CCIThink_Technical_Report_Draft.docx` and PDF; Markdown source follows Chapters 1–5, references and appendices. |
| Requested IMRaD manuscript | `docs/paper/CCIThink_IMRaD_Draft.docx` and PDF, with the confirmed author names. |
| APA 7 citations | Author/date citations, titled references, italic reference titles and hanging indents; unnamed course/source documents are not assigned invented authors. |
| Appendices and user guide | Both reports include repository link, dataset dictionary/sample, evidence locations, test cases, reproduction/user guide and AI disclosure. Browser screenshots and additional result tables are in the repository. |
| Presentation and defense | 12-slide PPTX/PDF plus speaker notes in `docs/paper`; suggested 10–15 minutes and separate 5-minute Q&A. |
| No fabricated findings / responsible AI | Results are generated from retained artifacts; no participants, interviews, survey percentages or successful live LLM claims are invented. AI-assisted code/examples/drafting disclosed. |

Before submission, the named authors still need to review and understand the code and draft, check instructor-specific formatting/disclosure expectations, and confirm appropriate source permissions/current institutional facts. Those are academic/source-review responsibilities, not software features that this update can certify. No grade, instructor sign-off or real-user effectiveness is claimed.
