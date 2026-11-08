# Project proposal: CCIThink

Authors: Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.

Course: Principles of Artificial Intelligence and Data Science.

## Problem and objective

Students need to find information about CCIT programs, subjects, faculty, scholarships, organizations, and department activities. The project proposes a Python chatbot with a local FAQ classifier and a separate analysis page. Its measurable task is classifying a question to a known FAQ label. Staff workload, waiting time, and student satisfaction are not measured.

## Dataset

The current approved-topic implementation uses 220 active source FAQs and 1,825 labeled questions. Supplied titles and alternatives provide 945 training examples; 440 validation and 440 test examples were AI-authored and fixed separately. FAQ-020 was retired by user request, and the other IDs and examples retain their wording and split. Original source text and source/currency metadata remain traceable. Broader redistribution permission and institutional currency are unconfirmed. See data/README.md.

## Proposed method and outputs

The workflow validates a CSV, reports missing/invalid/duplicate rows, standardizes text, describes lengths and label/language counts, and generates at least three EDA charts. A standard-Python multinomial Naive Bayes classifier compares four fixed feature/smoothing settings using validation macro F1. The selected model is evaluated on separate test questions with accuracy, macro metrics, a confusion matrix, per-class results, and a majority baseline.

The outputs are a working Flask chat and analysis interface, model/report/CSV artifacts, five charts, a five-chapter technical report with APA-style references, the requested IMRaD, and a 12-slide presentation. Setup, a user guide, test cases, and additional screenshots are included as required by the original course handout in FINAL_PROJECT.pdf.

## Limits and ethics

The project is a classroom demonstration using constructed examples, not an independently evaluated student service. No private student records are needed. Source support checks remain separate from classification, and unknown or ambiguous questions must not receive invented facts. AI assistance in coding, examples, debugging, and drafting is disclosed. Each author must review the documents, understand the implementation, and follow instructor-specific disclosure and source-permission requirements.
