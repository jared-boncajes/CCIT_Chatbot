"""The expanded model is reproducible, leak-free and usable by the app."""
import json
import subprocess
import sys
from pathlib import Path

from app import create_app
from chatbot.intent_model import IntentModel, knowledge_fingerprint
from research.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]


def test_all_labels_have_training_and_frozen_holdout_examples():
    knowledge = json.loads((ROOT / 'data/knowledge.json').read_text())
    ids = {r['id'] for r in knowledge}
    rows, profile = load_dataset(ROOT / 'data/question_dataset_v3.csv', ids)
    assert len(ids) == 221
    assert profile['split_counts'] == {'train': 951, 'validation': 442, 'test': 442}
    for split in ('train', 'validation', 'test'):
        assert {r['faq_id'] for r in rows if r['split'] == split} == ids
    assert profile['quality']['retained_rows'] == profile['quality']['input_rows'] == 1835
    assert not profile['quality']['duplicate_rows_removed']
    assert not profile['quality']['missing_rows_removed']
    assert not profile['quality']['invalid_rows_removed']
    artifact = json.loads((ROOT / 'research/results-v3/model.json').read_text())
    assert set(artifact['class_counts']) == ids
    assert artifact['metadata']['knowledge_sha256'] == knowledge_fingerprint(knowledge)
    assert artifact['metadata']['dataset_sha256'] == profile['sha256']
    assert set(artifact['metadata']['training_sample_ids']) == {r['sample_id'] for r in rows if r['split'] == 'train'}
    # Refit only the recorded winner, never select using test performance.
    fitted = IntentModel.fit([r for r in rows if r['split'] == 'train'],
                             alpha=artifact['alpha'], ngram_max=artifact['ngram_max'])
    assert fitted.artifact['term_counts'] == artifact['term_counts']
    assert fitted.artifact['vocabulary'] == artifact['vocabulary']


def test_dataset_builder_reproduces_frozen_bytes():
    paths = [ROOT / 'data/question_dataset_v3.csv', ROOT / 'data/question_dataset_v3_audit.json']
    before = [p.read_bytes() for p in paths]
    subprocess.run([sys.executable, str(ROOT / 'tools/build_question_dataset_v3.py')],
                   cwd=ROOT, check=True, capture_output=True)
    assert before == [p.read_bytes() for p in paths]


def test_app_loads_expanded_model_and_serves_current_analysis():
    app = create_app({'TESTING': True, 'CHAT_MODE': 'faq', 'API_KEY': None})
    client = app.test_client()
    assert client.get('/api/health').get_json()['intent_model_ready']
    report = client.get('/api/analysis').get_json()['report']
    assert len(report['labels']) == 221
    assert report['dataset']['quality']['retained_rows'] == 1835
    for question, expected in [('Who teaches BSCS?', 'FAQ-018'), ('BSCS OJT hours', 'FAQ-207')]:
        prediction = client.post('/api/classify', json={'message': question})
        assert prediction.status_code == 200
        assert prediction.get_json()['predictions'][0]['faq_id'] == expected
    assert client.get('/analysis').status_code == 200
    for name in ('class_distribution', 'question_lengths', 'language_distribution',
                 'validation_experiment', 'test_confusion'):
        figure = client.get(f'/analysis/figures/{name}.png')
        assert figure.status_code == 200 and figure.data.startswith(b'\x89PNG')


def test_diffuse_model_scores_do_not_displace_source_ranking():
    from chatbot.retriever import retrieve

    class WeakModel:
        def predict(self, question):
            return [{'faq_id': 'B', 'score': .49}, {'faq_id': 'A', 'score': .2}]

    records = [dict(id=label, question='Which laboratories exist?', answer='The AI laboratory exists.',
                    category='facilities', verification_status='verified') for label in ('A', 'B')]
    assert retrieve('labs', records, WeakModel()) == retrieve('labs', records)
