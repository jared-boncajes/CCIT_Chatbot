# November 10 presentation guide

Explain the student need: finding reliable department information quickly. Show how the interface sends a question to Flask, retrieves reviewed JSON records, then asks the configured Gemini or OpenAI model to summarize only that evidence. This lightweight approach keeps a small FAQ dataset maintainable by three group members without training a model or maintaining a database.

Before presenting, confirm the currency of the imported About CCIT document, configure an available model and key, test the following sequence, and capture real screenshots. Label FAQ mode accurately; do not present retrieval-only answers as AI generation.

1. Open the interface and explain readiness/mode.
2. Ask about programs using the document's actual question.
3. Inspect answer and source IDs.
4. Ask a paraphrase or Filipino variant and compare the source.
5. Ask a question outside the dataset; show the unknown-answer response.
6. Ask for private grades; explain the privacy boundary.
7. Clear the chat and demonstrate loading/error feedback.

Discuss executed tests from testing.md, source freshness, lexical retrieval limitations, and the need to review model outputs. Both Gemini and OpenAI use their maintained official SDKs. Gemini was added to allow use of an AI Studio key and any free-tier quota available to the selected account/model; no live provider comparison or free-quota guarantee is claimed. Future work: broader multilingual evaluation, stronger retrieval, and production deployment hardening. Use the actual screenshots in `docs/screenshots/` and the recorded retrieval results in `docs/evaluation.json`. The revised Figma layout and 14 browser scenarios have been checked; live AI remains untested. Explain that FAQ-mode screenshots demonstrate source retrieval and interface behavior, not AI generation.
