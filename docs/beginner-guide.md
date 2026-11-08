# Reading and explaining CCIThink

Start by running the app in FAQ mode with the commands in README.md. Ask `it dept chair`, then an unsupported question such as a staff member's salary. Try `prereqs` to see why the app asks for a subject and program.

## Read the code in this order

1. `app.py`: `create_app` loads knowledge and the model. `chat` checks the input, handles private requests and follow-ups, retrieves sources, and prepares the reply. The numbered comments describe the request flow.
2. `chatbot/retriever.py`: `expand_shorthand` expands a fixed list of short forms. `tokens` keeps meaningful words. `retrieve` filters sources and scores word support. Unknown names and program codes are not freely guessed.
3. `chatbot/scope.py`: checks whether a subject, program, year, or other detail is needed before answering.
4. `chatbot/conversation.py` and `roster.py`: retain small, allowed selectors for follow-ups and filter the dated representative roster. They do not accept user-supplied facts as context.
5. `chatbot/answers.py`: presents text from the selected answer. The original wording remains in source metadata.
6. `chatbot/intent_model.py`: trains and runs the Naive Bayes classifier using ordinary Python counts and math.
7. `research/dataset.py`, `research/evaluation.py`, and `analyze.py`: validate the CSV, calculate metrics, compare settings, and save the model, report, and charts.
8. `research/web.py`, `templates/analysis.html`, and `static/js/analysis.js`: show the analysis and call the local prediction endpoint.
9. `templates/index.html`, `static/js/script.js`, and `static/css/style.css`: display the chat, send requests, and handle loading, retry, and safe text rendering.

`chatbot/ai_service.py` and `errors.py` handle optional provider requests and readable errors. They are not required for FAQ mode or the local classifier. `check_ai.py` checks private provider configuration without printing keys.

## What the classifier actually learns

Each training row is a question and an FAQ ID. The model counts which words occur for each label. It does not learn department facts from the internet or invent answers.

For a label, the calculation uses:

```text
prior = training questions with this label / all training questions
likelihood = (count of a word for the label + alpha) /
             (all word counts for the label + alpha * vocabulary size)
score = log(prior) + sum(question word count * log(likelihood))
```

Smoothing (`alpha`) gives unseen word combinations a small count. Logarithms let the code add scores instead of multiplying many small values. The label with the largest score ranks first. Normalized scores are not calibrated confidence or proof of source support.

A small worked example: label A has `apple apple`; label B has `pear`. Both priors are 1/2. With alpha 1 and two vocabulary words, the likelihood of `apple` is 3/4 for A and 1/3 for B. The normalized score for A is `(3/8) / (3/8 + 1/6) = 9/13`. A unit test checks this exact result.

## Why the dataset has three splits

The 945 training questions learn the vocabulary and counts. The 440 validation questions choose among four fixed unigram/bigram and smoothing settings. The 440 test questions evaluate the chosen setting. Validation and test questions are AI-authored constructed examples, not real student messages.

All remaining questions keep their original split and wording. FAQ-020 and its examples were removed by user request; the retained laboratory information is FAQ-189. A changed corpus produces revised scores, not an independent new evaluation.

## How to explain the charts

- Class distribution: how many authored questions belong to each FAQ.
- Question lengths: how short or long questions are; valid long examples are retained.
- Language distribution: all current examples are English, which exposes a coverage gap.
- Validation comparison: how the four fixed settings compare before testing.
- Confusion matrix: which correct labels were predicted as other labels.

Accuracy is the fraction of correct predictions. Macro F1 gives each label equal weight when averaging precision/recall results. The current 80.2% classifier accuracy is separate from source-selection regression checks and does not mean every factual answer is current or correct.

## Training and adding knowledge

Run `python tools/build_dataset.py`, then `python analyze.py`, then restart Flask. The builders use `data/knowledge.json` and the explicit holdouts in `data/holdouts.json`. The saved model is rejected if its knowledge fingerprint does not match the current source.

A new FAQ needs a unique stable ID, its actual source answer, alternative questions, keywords, and honest source/currency metadata. Dataset labels and holdouts must match the active IDs. Do not alter held-out questions to improve a score you already inspected. A fresh accuracy claim needs an independent evaluation protocol.

## Demonstration and defense

Show a supported answer, a short form, a follow-up, an ambiguous request, a missing fact, and a local classifier prediction. Explain one real mistake from `research/results/test_predictions.csv`. Then explain the limits: constructed examples, English-only model evaluation, sparse questions per class, overlapping labels, unconfirmed institutional currency, and optional external-provider privacy.

The original course handout is `docs/FINAL_PROJECT.pdf`. The proposal, five-chapter report, IMRaD, data dictionary, charts, test evidence, and slides remain in the repository. The slides target a 10–15-minute presentation followed by 5 minutes of questions.

AI assistance is disclosed in the reports and README. Each member should be able to explain the methodology and the code they submit; a simpler folder structure does not replace studying or verifying the work.
