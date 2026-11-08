# Project proposal

**Title:** CCIThink: A Source-Grounded CCIT Information Chatbot with Explainable FAQ Classification and Data Analysis

**Authors:** Boncajes, Rhian Jared D.; Marcos, Maricar N.; Carandang, Jamie Pearl U.

**Course:** Principles of Artificial Intelligence and Data Science. **Topic approval:** confirmed by the user, November 8, 2026.

## Problem and objectives

The project addresses finding relevant information within a supplied department FAQ document when users phrase the same question differently. It combines an existing CCIT chat interface with an inspectable supervised classification and analysis workflow. It does not predict student performance or claim measured staff-workload reduction.

The general objective is to develop and evaluate a Python application that transforms a documented question dataset into useful FAQ-intent predictions and interpretable findings. Specific objectives are CSV dataset management, appropriate text preprocessing, descriptive EDA with at least three charts, an implemented classifier, a meaningful parameter comparison, appropriate split-based evaluation and responsible-use documentation.

## Dataset and proposed method

The source is 22 FAQs from the user-supplied About CCIT document. A separate corpus contains 264 AI-assisted constructed questions, not real student transcripts. Its six fields and permission status are documented in `data/README.md`. The fixed split has 176 training, 44 validation and 44 testing questions, with every FAQ label represented in each partition. This is a demonstration corpus, not evidence of real student inquiry distribution.

Multinomial Naive Bayes is implemented directly in Python using text counts. The experiment compares unigram versus unigram-plus-bigram features and additive smoothing of 1.0 versus 0.5. Training fits vocabulary and counts; validation macro F1 selects the configuration; a frozen test set and majority baseline assess the selected model. Metrics include accuracy, precision, recall, F1 and a confusion matrix.

## Expected outputs and scope

Outputs are the preserved chat UI, a separate analysis/results page, documented CSV and data dictionary, runnable source code, five visualizations, a trained local classifier, complete prediction/error artifacts, an IMRaD manuscript, a five-chapter report and a defense presentation. The learner assists ranking after existing source-support checks; it cannot invent department facts or access private records.

The corpus, labels and institutional facts need author/department review before broad use. AI assistance is disclosed, and students must understand the submitted implementation. No independent human study or successful live AI-generation claim forms part of this proposal.

**Implementation note:** this proposal is retained as a submission artifact; the accompanying analysis has now been executed. Its actual results are reported separately rather than described as expected outcomes here.
