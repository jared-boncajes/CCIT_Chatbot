"""Read-only project-analysis page. Training/imports run through the local CLI."""
import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory

from chatbot.conversation import is_private_question

analysis_blueprint = Blueprint('analysis', __name__)
FIGURES = {
    'class_distribution.png': ('FAQ class distribution', 'Counts reflect the supplied dataset and its constructed examples; they do not represent actual student demand.'),
    'question_lengths.png': ('Question lengths', 'Short and long questions are retained. Length outliers are descriptions, not automatic reasons to discard valid text.'),
    'language_distribution.png': ('Authoring-language distribution', 'English, Filipino and Taglish tags describe constructed wording; they are approximate and were not independently annotated.'),
    'validation_experiment.png': ('Parameter experiment', 'Four fixed configurations were compared on validation data. The test set did not choose the model.'),
    'test_confusion.png': ('Test confusion matrix', 'Rows are actual FAQ labels; columns are predictions. Only two held-out questions are available per class.'),
}


def read_report():
    path = Path(current_app.config['ANALYSIS_ROOT']) / 'report.json'
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(report, dict) or report.get('schema_version') != 1:
            return None
        return report
    except (OSError, ValueError):
        return None


@analysis_blueprint.get('/analysis')
def analysis():
    report = read_report()
    return render_template('analysis.html', report=report, figures=FIGURES,
                           model_ready=current_app.config['INTENT_MODEL'] is not None)


@analysis_blueprint.get('/api/analysis')
def analysis_data():
    report = read_report()
    if report is None:
        return jsonify(success=False, error='Run analyze.py to prepare the project analysis.'), 503
    return jsonify(success=True, report=report)


@analysis_blueprint.get('/analysis/figures/<filename>')
def analysis_figure(filename):
    if filename not in FIGURES:
        return jsonify(success=False, error='Figure not found.'), 404
    return send_from_directory(Path(current_app.config['ANALYSIS_ROOT']) / 'figures', filename)


@analysis_blueprint.post('/api/classify')
def classify():
    body = request.get_json(silent=True)
    message = body.get('message') if isinstance(body, dict) else None
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return jsonify(success=False, error='Enter a question between 1 and 1,000 characters.'), 400
    if is_private_question(message):
        return jsonify(success=False, error='Use public department questions; this demonstration cannot access private student records.'), 400
    model = current_app.config['INTENT_MODEL']
    if model is None:
        return jsonify(success=False, error='Run analyze.py and restart Flask to load a model matching the knowledge file.'), 503
    labels = {record['id']: record['question'] for record in current_app.config['KNOWLEDGE']}
    predictions = [{**item, 'title': labels[item['faq_id']]} for item in model.predict(message)[:3]]
    return jsonify(success=True, predictions=predictions,
                   note='Closed-set FAQ predictions. Scores are uncalibrated and do not establish that an answer is supported.')
