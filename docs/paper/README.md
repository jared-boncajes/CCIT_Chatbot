# Papers and defense materials

Authors: **Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.**

| Deliverable | Editable | PDF | Source |
| --- | --- | --- | --- |
| Requested IMRaD paper | [Word](CCIThink_IMRaD_Draft.docx) | [PDF](CCIThink_IMRaD_Draft.pdf) | [Markdown](imrad.md) |
| Professor-required five-chapter report | [Word](CCIThink_Technical_Report_Draft.docx) | [PDF](CCIThink_Technical_Report_Draft.pdf) | [Markdown](technical-report.md) |
| 12-slide defense deck | [PowerPoint](CCIThink_Defense.pptx) | [PDF](CCIThink_Defense.pdf) | [Slides and speaker notes](defense-slides.md) |

The documents are **drafts for author review**. They use the measured 28/44 classifier result (63.6% accuracy, macro F1 0.595) and distinguish it from software regression checks. They do not invent participants, student survey outcomes, current department verification or successful live AI generation. AI-assisted implementation, constructed examples and drafting are disclosed.

The technical report follows Chapters 1–5, references and appendices from the uploaded guidelines. The IMRaD version provides the requested article structure. Figures, experiment tables, dataset description, algorithm equations, actual limitations, references and reproduction instructions are included. See [reference notes](reference-notes.md), [guideline checklist](../guideline-compliance.md) and [user guide](../research-guide.md).

Regenerate using `python tools/build_project_documents.py` after installing `requirements-research.txt`. The generator reads `research/results/report.json`. If the dataset or experiment changes, update and review both the prose and outputs; do not silently tune against the current frozen test set.
