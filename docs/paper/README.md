# Papers and defense materials

Authors: **Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.**

| Deliverable | Editable | PDF | Source |
| --- | --- | --- | --- |
| Requested IMRaD paper | [Word](CCIThink_IMRaD_Draft.docx) | [PDF](CCIThink_IMRaD_Draft.pdf) | [Markdown](imrad.md) |
| Professor-required five-chapter report | [Word](CCIThink_Technical_Report_Draft.docx) | [PDF](CCIThink_Technical_Report_Draft.pdf) | [Markdown](technical-report.md) |
| 12-slide defense deck | [PowerPoint](CCIThink_Defense.pptx) | [PDF](CCIThink_Defense.pdf) | [Slides and speaker notes](defense-slides.md) |

The documents are **drafts for author review**. The IMRaD manuscript now uses clearer, formal language and reports the current **221-FAQ experiment**: 1,835 labeled questions; 951 training, 442 validation and 442 test; 365/442 correct test predictions (82.6% accuracy; macro F1 0.822). Definitions are given in ordinary language, with detailed implementation kept in the repository. Constructed questions, AI assistance and the lack of independent student evaluation remain disclosed. The roster and abbreviation fixes are application rules, not new classifier-training results.

The **five-chapter technical report and defense deck still document the original 22-FAQ experiment** (28/44 correct; 63.6% accuracy, macro F1 0.595). They are historical drafts and should be revised separately before presenting them as the current system. Their earlier numerical results must not be mixed with the updated IMRaD manuscript.

The technical report follows Chapters 1–5, references and appendices from the uploaded guidelines. The IMRaD version provides the requested article structure. Figures, experiment tables, dataset description, algorithm equations, actual limitations, references and reproduction instructions are included. See [reference notes](reference-notes.md), [guideline checklist](../guideline-compliance.md) and [user guide](../research-guide.md).

Regenerate just the current IMRaD manuscript using `python tools/build_imrad.py` after installing `requirements-research.txt`. It reads `research/results-v3/report.json` and writes matching Word, PDF and Markdown copies. `python tools/build_project_documents.py` also uses the new IMRaD content, while rebuilding the historical technical report and slides from `research/results/report.json`. If the dataset or experiment changes, update and review both the prose and outputs; do not tune against the current frozen test set.

The IMRaD layout follows the supplied Klarify example: centered title/authors/affiliation, full-width abstract and key terms, then two-column Roman-numbered Introduction, Methodology, Result, and Discussion with references. Its topic, authors, data, and results remain CCIThink’s. Regenerate with `python tools/build_imrad.py`. The expanded results include three newly supplied department-chair FAQs; existing holdouts were preserved.
