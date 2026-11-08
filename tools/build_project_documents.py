"""Build reviewable manuscripts and defense slides from measured project results.

Optional dependencies: requirements-research.txt. Run from the repository root.
The same content blocks generate Markdown, editable Word files and PDFs.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/paper'
AUTHORS = ['Boncajes, Rhian Jared D.', 'Marcos, Maricar N.', 'Carandang, Jamie Pearl U.']
TITLE = 'CCIThink: Development and Evaluation of a Source-Grounded CCIT Chatbot with Naive Bayes FAQ Classification'


def para(text):
    return {'kind': 'paragraph', 'text': ' '.join(text.split())}


def head(text, level=1):
    return {'kind': 'heading', 'text': text, 'level': level}


def bullets(items):
    return {'kind': 'bullets', 'items': items}


def table(caption, headers, rows, widths=None):
    return {'kind': 'table', 'caption': caption, 'headers': headers, 'rows': rows, 'widths': widths}


def figure(filename, caption):
    return {'kind': 'figure', 'path': ROOT / 'research/results/figures' / filename, 'caption': caption}


def cover(subtitle):
    return [{'kind': 'title', 'text': TITLE}, {'kind': 'center', 'text': subtitle},
            *[{'kind': 'center', 'text': name} for name in AUTHORS],
            {'kind': 'center', 'text': 'CCIT, FAITH Colleges'},
            {'kind': 'center', 'text': 'Principles of Artificial Intelligence and Data Science'},
            {'kind': 'center', 'text': 'November 2026 · Draft for author review'}, {'kind': 'pagebreak'}]


def content(report):
    profile, test, selected = report['dataset'], report['test'], report['selected']
    pct = lambda value: f'{100 * value:.1f}%'
    experiments = [[row['name'].replace('a=', 'alpha='), str(row['correct']) + '/44',
                    pct(row['accuracy']), f"{row['macro_f1']:.3f}"] for row in report['experiments']]
    abstract = [head('Abstract'), para(f'''
        This project developed CCIThink, a web-based department information chatbot for CCIT at FAITH Colleges,
        and added a reproducible data-science workflow while preserving its existing interface. The work addressed
        how a small, documented question dataset can support explainable FAQ classification without allowing a
        learned prediction to replace source evidence. Twenty-two FAQs from a supplied department document were
        paired with 264 AI-assisted constructed questions, allocated to 176 training, 44 validation and 44 test
        examples. The pipeline validated a CSV dataset, normalized text, summarized data quality, and produced five
        exploratory and evaluation figures. A standard-Python multinomial Naive Bayes implementation compared
        unigrams and unigrams plus bigrams under two smoothing settings. Validation macro F1 selected the
        unigram-plus-bigram model with alpha = 0.5. It correctly classified {test['correct']} of {test['samples']} test
        questions ({pct(test['accuracy'])} accuracy), with macro F1 = {test['macro_f1']:.3f}; a training-majority
        baseline obtained {pct(report['baseline']['accuracy'])} accuracy. These findings describe a controlled,
        constructed corpus, not real-world student accuracy. Errors, especially in some Filipino wordings and
        related academic intents, support using the classifier as a bounded ranking aid behind source checks.
        The completed prototype demonstrates dataset handling, machine learning, evaluation, visual interpretation
        and responsible-use documentation. Independent student-data evaluation and current department verification
        remain future work.
    '''), para('Keywords: department chatbot; FAQ classification; multinomial Naive Bayes; data analysis; responsible AI')]

    intro = [
        head('Background and problem', 2),
        para('''CCIThink addresses the practical task of locating department information in a supplied CCIT
        document. Its knowledge base covers programs, scholarships, faculty, facilities and related activities.
        A conversational interface can help users ask these questions in familiar wording, but useful behavior
        requires both relevant answer selection and clear boundaries around missing information. This project
        does not claim that staff workload, response delays or student satisfaction were measured before development.
        The need is framed as an information-access and classification problem rather than as a demonstrated
        reduction in administrative workload.'''),
        para('''The original system used reviewed FAQ records, lexical retrieval and optional Gemini or OpenAI
        answer generation. That combination alone did not demonstrate all of the course's data-science requirements.
        The final-project handout calls for dataset management, preprocessing, at least three visualizations, an
        implemented algorithm, task-specific evaluation, experimentation and an ethics discussion (Final project:
        AI-powered data analysis and prediction system, n.d.). The authors confirmed that the CCIT chatbot topic
        had instructor approval. The adaptation therefore treats selection of one of 22 FAQ intents as the supervised
        learning task and adds an analysis workflow alongside the existing chat interface.'''),
        head('Objectives and research questions', 2),
        para('''The general objective was to develop and evaluate a source-grounded department chatbot with a
        reproducible Python data-analysis and FAQ-classification component. Specific objectives were to document
        a relevant corpus, implement transparent cleaning, visualize its structure, implement a trainable classifier,
        compare prespecified configurations using validation data, evaluate the selected model on a separate test
        partition, and preserve source-support and privacy checks during application integration.'''),
        bullets([
            'RQ1: How accurately does the selected model classify held-out constructed questions into the 22 FAQ labels?',
            'RQ2: How do unigram versus unigram-plus-bigram features and smoothing alpha = 1.0 versus 0.5 affect validation performance?',
            'RQ3: Which observed errors and ethical constraints should limit use of the model inside the chatbot?',
        ]),
        head('Scope, limitations and significance', 2),
        para('''The project is an educational prototype for a small, fixed FAQ collection. It does not predict grades,
        assess individual students, provide private records, process enrollment transactions or verify current policy.
        Its contribution is an inspectable connection between dataset preparation, a learned text classifier and a
        working information interface. The study is relevant to students learning AI and Data Science because its
        counts, equations, errors and software behavior can be reproduced and explained. Department staff may
        review its information coverage, but deployment suitability and user benefit require additional evidence.'''),
    ]

    related = [
        head('Text classification and explainable learning', 2),
        para('''Multinomial Naive Bayes classifies text using feature counts, class priors and smoothed conditional
        likelihoods. Its conditional-independence assumption simplifies training and inference, while additive
        smoothing prevents unseen class-feature combinations from receiving zero likelihood. The scikit-learn
        documentation describes this formulation and distinguishes Laplace smoothing at alpha = 1 from Lidstone
        smoothing below 1 (Scikit-learn developers, n.d.-b). CCIThink implements the count-based calculation directly
        in Python rather than loading a pretrained text model. This makes its operation suitable for code explanation
        and a small course demonstration, but does not establish that it is the best classifier for the domain.'''),
        head('Related conversational system', 2),
        para('''Rasa Open Source provides a related example of a machine-learning framework for contextual text and
        voice assistants (Rasa, n.d.). Its repository also identifies the legacy open-source project as being in
        maintenance mode. CCIThink has a narrower scope: it ranks documented FAQ records and carries only a small
        program context for follow-ups, rather than implementing a general dialogue-management framework or
        transactional workflow. Rasa is discussed as a related system; it was not installed, evaluated or used as
        an experimental baseline in this project.'''),
        head('Evaluation concepts and identified opportunity', 2),
        para('''Accuracy gives the proportion of correct predictions, while per-class precision and recall describe
        different error types. Macro F1 averages the class-specific F1 scores and gives equal weight to every FAQ
        intent (Scikit-learn developers, n.d.-a). Reporting only a single overall percentage can hide classes that
        fail completely. A confusion matrix and language-tag breakdown therefore accompany the aggregate metrics.
        Naive Bayes score normalization also does not make scores reliable probabilities of correctness
        (Scikit-learn developers, n.d.-b). The opportunity addressed here is to expose these limitations while retaining
        source checks, instead of presenting a prebuilt language-model response as sufficient evidence of machine
        learning performance.'''),
    ]

    methods = [
        head('Design and data source', 2),
        para('''A developmental, computational study was conducted through software implementation and controlled
        offline evaluation. The unit of analysis was a question, not a student. No participants were recruited and no
        survey, interview, private transcript or usability outcome was collected. The supplied About CCIT document
        provided 22 FAQ answers and their corresponding labels (About CCIT, n.d.). Source transcription was checked
        during earlier development; institutional accuracy and currency were not independently confirmed. The source
        contains a college-name wording discrepancy that remains recorded in backend metadata.'''),
        para('''The question corpus was constructed with AI assistance from those 22 FAQ intents. Each intent has
        12 examples, fixed in authoring order before the first classifier experiment: eight training, two validation
        and two test examples. The resulting CSV contains 264 rows and six fields: sample_id, question, faq_id,
        split, language and provenance. The last two describe origin and approximate authoring language; neither
        enters the feature vector. Examples are not observed student demand, independently annotated language
        samples or an independently validated gold standard. Their size is sufficient to demonstrate the course
        workflow and expose errors across all 22 classes, but insufficient for population-level accuracy claims.'''),
        table('Table 1. Dataset allocation', ['Partition', 'Questions per FAQ', 'Total questions'],
              [['Training', '8', '176'], ['Validation', '2', '44'], ['Test', '2', '44'], ['Total', '12', '264']]),
        head('Collection and preprocessing procedures', 2),
        para('''The authoring examples are retained in question_examples.json and materialized as question_dataset.csv.
        A reproducible loader checks required columns, nonempty values, known FAQ IDs, allowed split and language
        values, unique sample IDs and a 1,000-character input limit. Missing or invalid rows and duplicates within the
        same split are removed and counted. Conflicting labels or an identical token sequence across different splits
        stop the run, because silently retaining such rows could contaminate evaluation. Exact overlap with the prior
        95-question development set was checked for validation and test examples; none was found. Related wording
        and parallel templates may still appear across partitions, which limits independence.'''),
        para('''Text is Unicode NFKC-normalized, case-folded, whitespace-normalized and standardized for curly
        apostrophes. A regular expression creates lowercase Latin-letter and number tokens, including internal
        apostrophes. Program abbreviations, numbers, question words and negations are retained; no stemming or
        stopword deletion is applied. Text is not imputed when absent. FAQ IDs are categorical targets; no one-hot
        encoding of language or provenance is needed because those fields are excluded. Token-length outliers are
        reported using the upper 1.5-IQR fence and retained when valid. An unusual question length is not itself
        evidence of an invalid public inquiry.'''),
        head('Features, algorithm and system workflow', 2),
        para('''The training vocabulary contains only features observed in the training partition. Candidate
        representations are unigram counts and unigram-plus-adjacent-bigram counts. For class c and question q,
        the implemented decision score is: score(c, q) = log P(c) + sum over t of x_t times log[(N_ct + alpha) /
        (N_c + alpha times |V|)]. Here x_t is the question feature count, N_ct is its training count in class c,
        N_c is the total feature count in that class, and |V| is the training-vocabulary size. Class priors come from
        training example frequencies. Scores are normalized using a numerically stable exponential calculation;
        they are described as uncalibrated relative scores. Inputs with no known features yield no prediction.'''),
        para('''Naive Bayes was selected for its transparent count-based implementation, low computational cost and
        suitability for a small text-classification demonstration, rather than a claim of optimality. JSON stores the
        trained counts and metadata without executable pickle objects. A knowledge fingerprint invalidates a model
        when source questions or answers change. The workflow is CSV loading, validation and normalization,
        descriptive analysis, training, validation-based selection, selected-model testing, figure/report export and
        application integration. All numerical analysis can run locally without an external AI API key.'''),
        para('''Inside the chatbot, privacy and unsupported-detail checks still apply. The learned score contributes
        only a fixed 0.25-times-score bonus to ranking among eligible lexical candidates; it cannot bypass topic,
        program, coverage or source checks. The standalone classifier is evaluated separately from this guarded
        application behavior. The chat homepage, styling and controls are preserved. A separate /analysis page
        presents data quality, charts, model comparison, errors and a local prediction demonstration. Optional
        Gemini/OpenAI answer generation remains a separate feature and was not used to obtain classifier metrics.'''),
        head('Experimental design and metrics', 2),
        para('''Four configurations were specified: unigram or unigram-plus-bigram features, each with alpha = 1.0
        or 0.5. Vocabulary, feature counts and priors were fitted on 176 training questions only. Validation macro F1
        selected the configuration; prespecified ties use validation accuracy, fewer n-grams and alpha closest to 1.
        The selected model was not refitted on validation questions. Only that selected configuration and a training
        majority-class baseline were evaluated on the frozen 44-question test partition. Test errors were inspected
        for discussion, not used to revise the corpus or retune this experiment. Re-running the scripts reproduces
        the same numerical outputs; it is not a new independent trial.'''),
        para('''For each class, precision = TP/(TP + FP), recall = TP/(TP + FN), and F1 = 2PR/(P + R), with zero
        used for undefined zero-denominator cases. Macro scores are arithmetic means across all 22 classes.
        Accuracy = correct predictions / all test questions. A confusion matrix shows actual-versus-predicted labels,
        and descriptive accuracy is also tabulated by approximate language tag. The 95 existing HTTP question
        checks and automated/browser checks are application regression evidence, not held-out classifier accuracy
        or human satisfaction measures.'''),
        head('Ethical considerations and responsible use', 2),
        para('''The dataset contains constructed public-information questions rather than private student records.
        Questions entered in the analysis demonstration are not persisted. Chat history and preferred names remain
        browser-tab-local; the backend does not store conversations. AI answer mode sends the question and selected
        source records to the configured provider, so external-provider handling must be considered before use with
        sensitive content. API keys remain in private environment settings. Department facts may be outdated, and
        source checking does not replace current institutional confirmation. No open redistribution license was
        supplied for the original department document. Its permitted use should be confirmed before broader release.
        AI assistance in code, dataset examples, tests and this draft is disclosed; the named authors must review and
        understand their submitted work in accordance with instructor policy.'''),
    ]

    results = [
        head('Dataset description and preprocessing results', 2),
        para(f'''The loader retained all {profile['quality']['retained_rows']} input examples. Missing rows,
        within-split duplicates and invalid rows were each zero in this constructed corpus; the cleaning code did
        not manufacture such problems to inflate its contribution. All 264 rows underwent format normalization.
        Seven token-length outliers above the upper fence of 11 tokens were retained. Questions ranged from
        {profile['token_lengths']['minimum']} to {profile['token_lengths']['maximum']} tokens, with mean
        {profile['token_lengths']['mean']:.2f}, median {profile['token_lengths']['median']:.0f} and sample standard
        deviation {profile['token_lengths']['stdev']:.2f}. Each FAQ has 12 examples by design. The approximate
        language tags comprise 176 English, 33 Filipino and 55 Taglish questions.'''),
        figure('class_distribution.png', 'Figure 1. Constructed class distribution. Equal counts reflect corpus design, not measured student demand.'),
        figure('question_lengths.png', 'Figure 2. Token-length distribution after normalization. Valid longer questions were retained.'),
        figure('language_distribution.png', 'Figure 3. Approximate authoring-language distribution. These tags are metadata, not independently verified annotations.'),
        head('Validation experiment and selected configuration', 2),
        table('Table 2. Prespecified configurations evaluated on validation data only',
              ['Features / smoothing', 'Correct', 'Accuracy', 'Macro F1'], experiments, [.45, .17, .19, .19]),
        para(f'''Unigrams with alpha = 1.0 obtained validation macro F1 = {report['experiments'][0]['macro_f1']:.3f}.
        The selected unigram-plus-bigram model with alpha = 0.5 obtained {selected['correct']} correct validation
        predictions ({pct(selected['accuracy'])}) and macro F1 = {selected['macro_f1']:.3f}. The validation result
        suggests that short word-order information and lighter smoothing helped this corpus. It does not establish
        a universally superior setting. The selected training vocabulary contained 810 features.'''),
        figure('validation_experiment.png', 'Figure 4. Validation macro F1 across the four fixed configurations. Test results did not select the model.'),
        head('Selected-model test results', 2),
        table('Table 3. Frozen-test performance; 44 questions, 22 classes',
              ['System', 'Accuracy', 'Macro precision', 'Macro recall', 'Macro F1'],
              [['Selected Naive Bayes', pct(test['accuracy']), f"{test['macro_precision']:.3f}", f"{test['macro_recall']:.3f}", f"{test['macro_f1']:.3f}"],
               ['Training-majority baseline', pct(report['baseline']['accuracy']), f"{report['baseline']['macro_precision']:.3f}", f"{report['baseline']['macro_recall']:.3f}", f"{report['baseline']['macro_f1']:.3f}"]], [.34, .17, .17, .16, .16]),
        para(f'''The selected model correctly classified {test['correct']} of {test['samples']} held-out questions,
        giving {pct(test['accuracy'])} accuracy and macro F1 = {test['macro_f1']:.3f}. Sixteen predictions were wrong.
        The majority baseline always selected FAQ-001, because all training classes were tied and the specified
        tie-break was alphabetical; it correctly classified 2 of 44 questions. The selected classifier therefore
        exceeded this weak baseline, but it still failed on more than one third of the small test partition.
        The gap between validation and test performance is a practical warning against interpreting the selected
        validation score as deployment accuracy.'''),
        figure('test_confusion.png', 'Figure 5. Test confusion matrix. Nonzero off-diagonal entries identify actual misclassifications; each row has only two examples.'),
        table('Table 4. Descriptive test results by approximate authoring-language tag', ['Tag', 'Correct / total', 'Accuracy'],
              [[language, f"{row['correct']} / {row['samples']}", pct(row['correct'] / row['samples'])]
               for language, row in test['by_language'].items()]),
        head('Errors, system behavior and verification', 2),
        para('''The two held-out examples for each of FAQ-002 (college overview), FAQ-006 (program offerings),
        FAQ-007 (IT definition) and FAQ-008 (CS definition) were all misclassified. Some definition questions were
        confused with faculty or mission questions, and several Filipino career questions were classified as the
        mission intent. Such results are consistent with sparse lexical coverage, shared phrasing and overlapping
        concepts, but causal explanations were not separately tested. The English-tagged set had 16/22 correct,
        Filipino 3/8 and Taglish 9/14. These small, constructed and approximately tagged groups do not support a
        claim about performance on all Filipino or English users.'''),
        para('''The integrated application passed the existing 95/95 HTTP source-support or answer-mode checks.
        The full automated suite passed 263 tests, and 26 browser scenarios covered the original chat behavior,
        concise bold replies, explicit recovery and the new analysis demonstration. Successful chat answers in
        these checks used FAQ mode; provider outages and safety payloads were explicitly simulated. These counts
        demonstrate checked software behavior, not 100% language understanding, current factual correctness,
        live AI-generation quality or measured student satisfaction. Timestamped reports and all test predictions
        are retained with the repository.'''),
    ]

    discussion = [
        head('Interpretation against the research questions', 2),
        para(f'''RQ1 is answered by {pct(test['accuracy'])} test accuracy and macro F1 = {test['macro_f1']:.3f}
        on the constructed corpus. RQ2 is answered by the validation comparison: the selected unigram-plus-bigram,
        alpha = 0.5 configuration had the highest validation macro F1 among the four settings. RQ3 is answered by
        the observed intent confusions, uneven descriptive language results and missing real-user evidence.
        Together, the findings favor a constrained supporting role for this learned model rather than autonomous
        authority over department answers.'''),
        para('''The results illustrate the distinction between classification and information reliability. A model
        can assign a strong relative score to a wrong FAQ, while a correct FAQ selection can still refer to an
        outdated institutional statement. Source-support guards, missing-information fallback and institutional
        review therefore address different concerns from classifier accuracy. The fixed 0.25 ranking bonus preserves
        this separation. No ablation study was run to estimate the bonus's causal effect on real-user answer quality;
        passing existing regression cases should not be interpreted as such an experiment.'''),
        head('Limitations and unexpected findings', 2),
        para('''The corpus is small, balanced by construction and AI-assisted. Closely related templates remain
        possible across partitions despite the absence of exact duplicate leakage. Only two test examples represent
        each class, so class-level metrics are unstable. Labels and language tags were not independently annotated,
        and inter-rater agreement was not measured. The classifier is closed-set and single-intent; unsupported,
        ambiguous, private and multi-intent questions are outside its numerical test task and are handled separately
        by application rules. The tokenizer does not provide robust morphology, spelling normalization or full
        non-ASCII-language coverage. These choices can disadvantage forms absent from training.'''),
        para('''The 95 development questions were used to improve earlier retrieval behavior and are not an
        independent generalization benchmark. No independent human assessment, task-completion timing,
        satisfaction survey, controlled workload comparison or production-load test was conducted. Successful
        live Gemini/OpenAI generation was not established in this environment because no private provider key
        was configured. The source's current factual accuracy remains unconfirmed. These limits prevent claims
        of institution-wide effectiveness or production readiness.'''),
        head('Practical recommendations', 2),
        bullets([
            'Obtain dated department confirmation for faculty, dean, scholarships, accreditation and official college-name wording.',
            'Collect permissioned or anonymized student questions, use independent label review, and create a fresh external test set before tuning further.',
            'Expand difficult Filipino/Taglish and ambiguous-intent examples; evaluate changes with grouped splits and explicit out-of-scope detection.',
            'Compare the current model with additional justified algorithms on training/validation data, then reserve new test evidence for final assessment.',
            'Evaluate score calibration, confidence rejection, accessibility, user task completion and deployment capacity before operational use.',
        ]),
    ]

    conclusion = [
        para('''CCIThink now combines the preserved department-chat interface with an inspectable data-science
        pipeline: CSV dataset handling, documented preprocessing, descriptive analysis, five figures, an implemented
        trainable algorithm, a validation experiment, frozen-test evaluation and a separate results demonstration.
        These completed components meet the technical coverage sought by the course guidelines while keeping
        the chatbot's answers concise and source-grounded.'''),
        para(f'''The selected classifier obtained {test['correct']}/{test['samples']} test predictions correct
        ({pct(test['accuracy'])}) and macro F1 = {test['macro_f1']:.3f}, exceeding the majority baseline but showing
        substantial errors. The supported conclusion is that the workflow functions as an educational prototype
        and that classification quality needs further evidence and improvement. The study does not establish
        current institutional accuracy, real-student effectiveness or successful live generative-AI service.
        Future work should prioritize authoritative data review and an independent, ethically collected question
        corpus rather than presenting the present results as final deployment performance.'''),
    ]

    references = [head('References'), *[{**para(text), 'kind': 'reference'} for text in [
        '*About CCIT*. (n.d.). [Department information document supplied with the project].',
        '*Final project: AI-powered data analysis and prediction system*. (n.d.). [Unpublished course handout, Principles of Artificial Intelligence and Data Science].',
        'Rasa. (n.d.). *Rasa Open Source* [Computer software]. GitHub. Retrieved November 8, 2026, from https://github.com/RasaHQ/rasa',
        'Scikit-learn developers. (n.d.-a). *Metrics and scoring: Quantifying the quality of predictions*. Scikit-learn user guide. Retrieved November 8, 2026, from https://scikit-learn.org/stable/modules/model_evaluation.html',
        'Scikit-learn developers. (n.d.-b). *Naive Bayes*. Scikit-learn user guide. Retrieved November 8, 2026, from https://scikit-learn.org/stable/modules/naive_bayes.html',
    ]]]

    appendices = [head('Appendices'), head('Appendix A. Repository and reproduction', 2),
        para('Repository: https://github.com/jared-boncajes/CCIT_Chatbot. Core analysis: analyze.py, chatbot/intent_model.py, research/dataset.py and research/evaluation.py. Setup and full user guide are in README.md and docs/research-guide.md.'),
        para('In an activated Python virtual environment, install requirements-research.txt. Run python analyze.py --dataset data/question_dataset.csv, then python app.py. Open / for chat and /analysis for the analysis demonstration. Use python -m pytest -q for automated checks. Numerical analysis can run with --no-figures when Matplotlib is unavailable.'),
        head('Appendix B. Dataset dictionary and permitted sample', 2),
        table('Table A1. CSV fields', ['Field', 'Meaning / role'], [
            ['sample_id', 'Unique example identifier; audit metadata, not a feature.'],
            ['question', 'Constructed public department question; only input to text features.'],
            ['faq_id', 'One of FAQ-001 through FAQ-022; supervised target linked to knowledge.json.'],
            ['split', 'Fixed train, validation or test assignment; not a feature.'],
            ['language', 'Approximate English, Filipino or Taglish authoring tag; excluded from features.'],
            ['provenance', 'AI-assisted constructed-example disclosure; not a student transcript.'],
        ], [.22, .78]),
        para('Sample training record: FAQ-018-Q02; question = "Who teaches BSCS?"; faq_id = FAQ-018; split = train; language = English. This is a constructed example, not a private student communication. The source PDF was not reclassified as openly licensed.'),
        head('Appendix C. Evidence and test cases', 2),
        para('research/results/report.json stores the experiment, confusion matrix, per-class metrics and language breakdown. test_predictions.csv lists every test prediction; experiments.csv lists the validation comparison. docs/screenshots contains actual browser evidence. Test cases cover hand-calculated Bayes probabilities, order-sensitive bigrams, invalid smoothing, cross-split leakage, conflicting labels, missing/stale artifacts, input validation and source guards.'),
        table('Table A2. Representative executed application checks', ['Input / action', 'Observed checked behavior'], [
            ['Do you guys offer BSCS?', 'Focused offering answer with bold degree name and no source/verification clutter.'],
            ['What time do the labs open?', 'Unsupported-detail fallback; a predicted topic cannot establish opening hours.'],
            ['Show my student grades', 'Privacy response in chat; prediction demo rejects the request.'],
            ['Who teaches BSCS? (analysis demo)', 'Local classifier predicts FAQ-018 without an AI provider call.'],
            ['New chat after a program follow-up', 'Clears program context and asks for clarification when required.'],
        ], [.42, .58]),
        {'kind': 'figure', 'path': ROOT / 'docs/screenshots/desktop.png',
         'caption': 'Figure A1. Actual browser screenshot of the preserved desktop home interface.'},
        {'kind': 'figure', 'path': ROOT / 'docs/screenshots/improvements/mobile-focused-answer.png',
         'caption': 'Figure A2. Actual mobile FAQ-mode answer with a bold key fact and concise text. The mode label distinguishes retrieval from AI generation.'},
        head('Appendix D. AI assistance and author review', 2),
        para('OpenAI Codex assistance was used for implementation, constructed question examples, tests, analysis scripts and manuscript drafting. Numerical findings were computed by the supplied scripts rather than fabricated. Before submission, the three named authors should verify citations and source permissions, review the corpus and outputs, explain the algorithm and code, confirm instructor-specific disclosure requirements, and adapt the draft as their own reviewed work. No participant study or independent human annotation is claimed.'),
    ]
    return dict(abstract=abstract, intro=intro, related=related, methods=methods, results=results,
                discussion=discussion, conclusion=conclusion, references=references, appendices=appendices)


def inline_runs(text):
    # Manuscript formatting only; input is project-authored content, not chat HTML.
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', str(text))
    return [(part[2:-2], 'bold') if part.startswith('**') and part.endswith('**')
            else (part[1:-1], 'italic') if part.startswith('*') and part.endswith('*') else (part, '') for part in parts]


def register_pdf_fonts():
    """Embed fonts so PDF viewers never substitute incompatible glyph metrics."""
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    bundled = Path(reportlab.__file__).parent / 'fonts'
    fallback = [bundled / name for name in ['Vera.ttf', 'VeraBd.ttf', 'VeraIt.ttf', 'VeraBI.ttf']]
    for family, windows, linux in [('PaperSerif', ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf'], 'LiberationSerif'),
                                    ('SlideSans', ['arial.ttf', 'arialbd.ttf', 'ariali.ttf', 'arialbi.ttf'], 'LiberationSans'),
                                    ('CodeMono', ['cour.ttf', 'courbd.ttf', 'couri.ttf', 'courbi.ttf'], 'LiberationMono')]:
        candidates = [[Path('C:/Windows/Fonts') / name for name in windows]]
        candidates += [[Path('/usr/share/fonts/truetype') / folder / (linux + '-' + suffix + '.ttf')
                        for suffix in ['Regular', 'Bold', 'Italic', 'BoldItalic']] for folder in ['liberation', 'liberation2']]
        paths = next((paths for paths in candidates if all(path.exists() for path in paths)), fallback)
        names = [family, family + '-Bold', family + '-Italic', family + '-BoldItalic']
        for name, path in zip(names, paths):
            pdfmetrics.registerFont(TTFont(name, str(path)))
        pdfmetrics.registerFontFamily(family, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3])


def write_markdown(blocks, path):
    lines = []
    for block in blocks:
        kind = block['kind']
        if kind in {'title', 'heading'}:
            lines.append('#' * (1 if kind == 'title' else block['level'] + 1) + ' ' + block['text'])
        elif kind in {'paragraph', 'center', 'reference'}:
            lines.append(block['text'])
        elif kind == 'pagebreak':
            lines.append('<!-- page break -->')
        elif kind == 'code':
            lines.append('```' + block.get('language', 'python') + '\n' + block['text'] + '\n```')
        elif kind == 'bullets':
            lines.append('\n'.join('- ' + item for item in block['items']))
        elif kind == 'table':
            lines.append(block['caption'])
            lines.append('| ' + ' | '.join(block['headers']) + ' |\n| ' + ' | '.join('---' for _ in block['headers']) + ' |')
            lines.extend('| ' + ' | '.join(map(str, row)) + ' |' for row in block['rows'])
        elif kind == 'figure':
            relative = Path('../../research/results/figures') / block['path'].name
            lines.append(f"![{block['caption']}]({relative.as_posix()})")
        lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def write_docx(blocks, path, document_title=TITLE, compact=False):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt
    from reportlab.lib.utils import ImageReader
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
    normal = document.styles['Normal']
    normal.font.name, normal.font.size = 'Times New Roman', Pt(11 if compact else 12)
    normal.paragraph_format.line_spacing = 1.15 if compact else 2
    normal.paragraph_format.space_after = Pt(0)
    for name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3']:
        document.styles[name].font.name = 'Times New Roman'
        document.styles[name].font.color.rgb = None
        document.styles[name].font.size = Pt(16 if name == 'Title' else 12)
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    header._p.append(field)
    for block in blocks:
        kind = block['kind']
        if kind == 'pagebreak':
            document.add_page_break()
        elif kind in {'title', 'heading'}:
            paragraph = document.add_paragraph(style='Title' if kind == 'title' else f"Heading {min(block['level'], 3)}")
            paragraph.add_run(block['text'])
            if kind == 'title' or block['level'] == 1:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
        elif kind in {'paragraph', 'center', 'reference'}:
            paragraph = document.add_paragraph()
            if kind == 'center':
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if kind == 'reference':
                paragraph.paragraph_format.left_indent = Inches(.5)
                paragraph.paragraph_format.first_line_indent = Inches(-.5)
            for text, emphasis in inline_runs(block['text']):
                run = paragraph.add_run(text)
                run.bold, run.italic = emphasis == 'bold', emphasis == 'italic'
        elif kind == 'bullets':
            for item in block['items']:
                document.add_paragraph(item, style='List Bullet')
        elif kind == 'code':
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.line_spacing = 1
            paragraph.paragraph_format.keep_together = True
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(10)
            run = paragraph.add_run(block['text'])
            run.font.name, run.font.size = 'Consolas', Pt(9)
        elif kind == 'table':
            document.add_paragraph(block['caption'], style='Caption')
            grid = document.add_table(rows=1, cols=len(block['headers']))
            grid.style = 'Light Shading Accent 1'
            for cell, text in zip(grid.rows[0].cells, block['headers']):
                cell.text = text
            for row in block['rows']:
                for cell, text in zip(grid.add_row().cells, row):
                    cell.text = str(text)
            for row in grid.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.line_spacing = 1
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
        elif kind == 'figure':
            width, height = ImageReader(str(block['path'])).getSize()
            document.add_picture(str(block['path']), width=Inches(min(6.3, 7 * width / height)))
            image_paragraph = document.paragraphs[-1]
            image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            image_paragraph.paragraph_format.line_spacing = 1
            image_paragraph.paragraph_format.keep_with_next = True
            caption = document.add_paragraph(block['caption'], style='Caption')
            caption.paragraph_format.line_spacing = 1
    document.core_properties.title = document_title
    document.core_properties.author = '; '.join(AUTHORS)
    document.core_properties.subject = 'AI-assisted research draft; measured offline evaluation'
    document.save(path)


def write_pdf(blocks, path, document_title=TITLE, compact=False):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib.utils import ImageReader
    styles = getSampleStyleSheet()
    body = ParagraphStyle('ManuscriptBody', fontName='PaperSerif', fontSize=11 if compact else 12, leading=16 if compact else 22,
                          spaceAfter=8, alignment=TA_JUSTIFY, splitLongWords=True)
    center = ParagraphStyle('ManuscriptCenter', parent=body, alignment=TA_CENTER, spaceAfter=12)
    title = ParagraphStyle('ManuscriptTitle', parent=center, fontName='PaperSerif-Bold', fontSize=17, leading=23, spaceBefore=78, spaceAfter=34)
    h1 = ParagraphStyle('ManuscriptH1', parent=body, fontName='PaperSerif-Bold', fontSize=14, leading=19,
                        alignment=TA_CENTER, spaceBefore=18, spaceAfter=12, keepWithNext=True)
    h2 = ParagraphStyle('ManuscriptH2', parent=h1, fontSize=12, leading=17, alignment=0, spaceBefore=12, spaceAfter=6)
    caption = ParagraphStyle('ManuscriptCaption', parent=body, fontName='PaperSerif-Italic', fontSize=10, leading=14, spaceAfter=10)
    cell_style = ParagraphStyle('ManuscriptCell', parent=body, fontSize=9.5, leading=12, spaceAfter=0, alignment=0)
    reference_style = ParagraphStyle('ManuscriptReference', parent=body, leftIndent=36, firstLineIndent=-36, alignment=0)
    code_style = ParagraphStyle('CodeBlock', fontName='CodeMono', fontSize=9, leading=12,
                               leftIndent=8, spaceBefore=6, spaceAfter=10)

    def markup(text):
        return ''.join(('<b>' + html.escape(part) + '</b>') if emphasis == 'bold' else
                       ('<i>' + html.escape(part) + '</i>') if emphasis == 'italic' else html.escape(part)
                       for part, emphasis in inline_runs(text))

    story = []
    for block in blocks:
        kind = block['kind']
        if kind in {'paragraph', 'center', 'title', 'heading', 'reference'}:
            style = title if kind == 'title' else center if kind == 'center' else reference_style if kind == 'reference' else (h1 if block['level'] == 1 else h2) if kind == 'heading' else body
            story.append(Paragraph(markup(block['text']), style))
        elif kind == 'pagebreak':
            story.append(PageBreak())
        elif kind == 'code':
            story.append(KeepTogether([Preformatted(block['text'], code_style, maxLineLength=83)]))
        elif kind == 'bullets':
            for item in block['items']:
                story.append(Paragraph('• ' + markup(item), body))
        elif kind == 'table':
            story.append(Paragraph(markup(block['caption']), caption))
            data = [[Paragraph('<b>' + markup(value) + '</b>', cell_style) for value in block['headers']]]
            data += [[Paragraph(markup(value), cell_style) for value in row] for row in block['rows']]
            count = len(block['headers'])
            weights = block['widths'] or ([.34, .66] if count == 2 else [1 / count] * count)
            grid = Table(data, colWidths=[468 * value for value in weights], repeatRows=1, hAlign='LEFT')
            grid.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4eeee')),
                ('LINEBELOW', (0, 0), (-1, 0), .8, colors.HexColor('#84201c')),
                ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#dddddd')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7), ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            story.extend([grid, Spacer(1, 12)])
        elif kind == 'figure':
            width, height = ImageReader(str(block['path'])).getSize()
            scale = min(468 / width, 430 / height)
            story.append(KeepTogether([Image(str(block['path']), width=width * scale, height=height * scale),
                                      Paragraph(markup(block['caption']), caption)]))

    def page(canvas, document):
        canvas.setTitle(document_title)
        canvas.setAuthor('; '.join(AUTHORS))
        canvas.setFont('PaperSerif', 12)
        canvas.drawRightString(540, 756, str(document.page))
    SimpleDocTemplate(str(path), pagesize=letter, leftMargin=72, rightMargin=72,
                      topMargin=72, bottomMargin=65).build(story, onFirstPage=page, onLaterPages=page)


def slides(report):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    test = report['test']
    entries = [
        ('CCIThink', ['CCIT information chatbot + explainable FAQ classification', *AUTHORS, 'Principles of Artificial Intelligence and Data Science · November 2026'], None,
         'Introduce the approved topic and team. Explain that this is a small educational prototype, not a student-record or grade-prediction system. About 45 seconds.'),
        ('Problem and objectives', ['Find answers within 22 documented department FAQs.', 'Preserve the existing chat UI and source-support checks.', 'Demonstrate data preparation, learning, evaluation and interpretation.'], None,
         'Frame information access as the project problem. Do not claim measured workload reduction or student satisfaction. About 1 minute.'),
        ('Dataset and provenance', ['264 AI-assisted constructed questions; 22 FAQ target labels.', '176 training / 44 validation / 44 test; fixed assignments.', 'Not real student conversations; no private records.', 'Eight training, two validation and two test questions per label.'], 'class_distribution.png',
         'Show question_dataset.csv and the data dictionary. Explain why a small corpus can demonstrate the workflow but cannot establish real-world effectiveness. About 1 minute.'),
        ('Preprocessing and EDA', ['Validate schema, label IDs, split membership and input limits.', 'Reject label conflicts and cross-split duplicates.', '264 normalized; 0 missing, duplicate or invalid rows removed.', 'Mean length 7.08 tokens; 7 longer valid questions retained.'], 'question_lengths.png',
         'Demonstrate actual cleaning statistics, not synthetic claims of dirty real data. Explain why outlier lengths were retained and why labels/language metadata are not features. About 1 minute.'),
        ('Language coverage', ['176 English / 33 Filipino / 55 Taglish authoring tags.', 'Tags are approximate, not independently annotated.', 'The corpus is balanced by FAQ, not sampled from student demand.'], 'language_distribution.png',
         'This is the third EDA visualization. Discuss representativeness and language bias, and distinguish designed counts from observed real student behavior. About 45 seconds.'),
        ('Implemented algorithm', ['Multinomial Naive Bayes, implemented in standard Python.', 'Count unigrams or unigrams plus adjacent bigrams.', 'Learn vocabulary and class-feature counts on training data only.', 'Additive smoothing avoids zero likelihoods; scores are uncalibrated.'], None,
         'Open chatbot/intent_model.py. Explain the log-prior plus feature-count-weighted log-likelihood equation. State the conditional-independence assumption and why it is imperfect for language. About 90 seconds.'),
        ('Validation experiment', ['Four fixed feature/smoothing configurations.', 'Choose using validation macro F1, not test accuracy.', 'Selected: unigrams + bigrams, alpha = 0.5.', 'Validation: 31/44 correct; macro F1 = 0.663.'], 'validation_experiment.png',
         'Explain each axis and the tie-breaking rule. Training and validation remain separate; the selected model was not refitted on validation data. About 1 minute.'),
        ('Frozen-test results', [f"28/44 correct: {100 * test['accuracy']:.1f}% accuracy.", f"Macro F1 = {test['macro_f1']:.3f}; macro precision = {test['macro_precision']:.3f}.", 'Majority-class baseline: 2/44 correct (4.5%).', '16 mistakes; only two test questions per label.'], 'test_confusion.png',
         'Interpret the confusion matrix and the limits of the baseline. Do not call the classifier perfect or generalize its percentage to all users. About 1 minute.'),
        ('Error analysis', ['English-tagged test: 16/22 correct.', 'Filipino-tagged test: 3/8; Taglish: 9/14.', 'Overview, offerings and IT/CS definitions were difficult.', 'Small constructed groups do not establish population differences.'], None,
         'Open test_predictions.csv and show an actual mistake. Explain sparse wording and overlapping intents as plausible, untested explanations. About 1 minute.'),
        ('Working demonstration', ['Run python analyze.py, then python app.py.', 'Use /analysis for charts, cleaning, metrics and predictions.', 'Use / for the preserved chat interface and short bold answers.', 'ML only adds a bounded ranking bonus after source checks.', '263 automated tests; 26 browser scenarios; 95/95 chat checks.'], None,
         'Demonstrate Who teaches BSCS? on the analysis page and the chat. Then show an unsupported detail falling back. Explain that the 95 checks are regression tests, not classifier hold-out accuracy. About 90 seconds.'),
        ('Ethics and limitations', ['No private student records; no stored chat transcript.', 'Department facts and source permissions still need appropriate review.', 'AI assistance is disclosed; every author must understand the code.', 'No participant study, production-load result or successful live LLM claim.'], None,
         'Discuss language bias, source currency and provider privacy. Note that optional AI answer mode sends selected information to the chosen provider. About 1 minute.'),
        ('Conclusion and next steps', ['A reproducible AI/Data Science workflow now supports the chatbot.', 'The classifier outperformed a weak baseline but needs improvement.', 'Next: confirmed facts, permissioned student examples, independent labels and a fresh test set.', 'Questions and defense discussion'], None,
         'Answer the three research questions briefly. Reserve the professor-required 5 minutes after the 10–15 minute presentation for questions. Do not claim field effectiveness. About 45 seconds.'),
    ]
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
    pdf = canvas.Canvas(str(OUT / 'CCIThink_Defense.pdf'), pagesize=(960, 540))
    outline = []
    for index, (title, points, image, notes) in enumerate(entries, 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        shape = slide.shapes.add_shape(1, 0, 0, presentation.slide_width, Inches(.16))
        shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string('A71917'); shape.line.fill.background()
        box = slide.shapes.add_textbox(Inches(.55), Inches(.45), Inches(12.2), Inches(.8))
        box.text_frame.text = title
        box.text_frame.paragraphs[0].font.size = Pt(30)
        box.text_frame.paragraphs[0].font.bold = True
        width = 6.1 if image else 12.1
        body = slide.shapes.add_textbox(Inches(.6), Inches(1.55), Inches(width), Inches(5.25))
        body.text_frame.word_wrap = True
        for item_index, point in enumerate(points):
            paragraph = body.text_frame.paragraphs[0] if item_index == 0 else body.text_frame.add_paragraph()
            paragraph.text = '• ' + point
            paragraph.font.size = Pt(22 if len(points) < 5 else 20)
            paragraph.space_after = Pt(22)
        if image:
            slide.shapes.add_picture(str(ROOT / 'research/results/figures' / image), Inches(6.95), Inches(1.65), width=Inches(5.8))
        slide.notes_slide.notes_text_frame.text = notes
        pdf.setFillColor(colors.HexColor('#a71917')); pdf.rect(0, 528, 960, 12, fill=1, stroke=0)
        pdf.setFillColor(colors.black); pdf.setFont('SlideSans-Bold', 30); pdf.drawString(40, 477, title)
        y = 410
        for point in points:
            for line in simpleSplit('• ' + point, 'SlideSans', 20, 430 if image else 870):
                pdf.setFont('SlideSans', 20); pdf.drawString(43, y, line); y -= 27
            y -= 17
        if image:
            pdf.drawImage(str(ROOT / 'research/results/figures' / image), 505, 120, width=420, height=300, preserveAspectRatio=True, anchor='c')
        pdf.setFont('SlideSans', 10); pdf.drawRightString(920, 23, f'CCIThink · {index}/12')
        pdf.showPage()
        outline.extend([f'## Slide {index}: {title}', '', *['- ' + point for point in points], '', '**Speaker notes:** ' + notes, ''])
    presentation.save(OUT / 'CCIThink_Defense.pptx')
    pdf.save()
    (OUT / 'defense-slides.md').write_text('\n'.join(outline), encoding='utf-8')


def main():
    report = json.loads((ROOT / 'research/results/report.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    register_pdf_fonts()
    parts = content(report)
    imrad = cover('IMRaD research manuscript') + parts['abstract'] + [head('Introduction')] + parts['intro'] + parts['related']
    imrad += [head('Methods')] + parts['methods'] + [head('Results')] + parts['results']
    imrad += [head('Discussion')] + parts['discussion'] + [head('Conclusion')] + parts['conclusion']
    imrad += [{'kind': 'pagebreak'}] + parts['references'] + parts['appendices']
    technical = cover('Five-chapter technical documentation') + parts['abstract']
    chapters = [('Chapter 1: Introduction', parts['intro']),
                ('Chapter 2: Review of Related Systems and Concepts', parts['related']),
                ('Chapter 3: Methodology', parts['methods']),
                ('Chapter 4: Results and Discussion', parts['results'] + parts['discussion'][:-2]),
                ('Chapter 5: Conclusion and Recommendations', parts['conclusion'] + parts['discussion'][-2:])]
    for name, blocks in chapters:
        technical += [{'kind': 'pagebreak'}, head(name)] + blocks
    technical += [{'kind': 'pagebreak'}] + parts['references'] + parts['appendices']
    for name, markdown_name, blocks in [('CCIThink_IMRaD_Draft', 'imrad.md', imrad),
                                        ('CCIThink_Technical_Report_Draft', 'technical-report.md', technical)]:
        write_markdown(blocks, OUT / markdown_name)
        write_docx(blocks, OUT / (name + '.docx'))
        write_pdf(blocks, OUT / (name + '.pdf'))
        print(f'Built {name}: Markdown, DOCX and PDF')
    slides(report)
    print('Built 12-slide defense presentation: PPTX, PDF and Markdown speaker notes')


if __name__ == '__main__':
    main()
