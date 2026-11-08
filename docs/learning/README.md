# Beginner walkthrough and defense guide

- [Editable Word document](CCIThink_Beginner_Walkthrough.docx)
- [PDF](CCIThink_Beginner_Walkthrough.pdf)
- [Markdown source](walkthrough.md)

The guide walks through the full project with the confirmed author names. Start with sections 1–5 to learn the chat flow and local classifier, then sections 6–9 for the UI, data and tests. Sections 10–12 contain a suggested seven-day build/practice plan, runnable examples and defense questions. The function/line index and complete file inventory are references for looking up the remaining files.

The backend was rewritten for readability using ordinary loops, descriptive variables and explicit decisions. The main chat handler has nine numbered steps, and the experiment has five. Classifier settings, source/privacy guards, concise bold answers, the existing UI and measured results are preserved. Small helper classes group related values; the guide explains how they work.

The guide teaches rebuilding and understanding the implementation. Record and describe work you actually perform. OpenAI Codex assistance in code, constructed examples, tests and documents remains disclosed; the materials do not invent a development history or individual contributions. Every team member should be able to trace a question and explain the model's actual 28/44 result.

Regenerate the guide after editing code so its line numbers and inventory remain current:

```powershell
py tools/build_walkthrough.py
```

Install `requirements-research.txt` first for Word/PDF export packages. The existing [research guide](../research-guide.md) covers setup and the professor's required demonstration; [papers and slides](../paper/README.md) are separate submission drafts.
