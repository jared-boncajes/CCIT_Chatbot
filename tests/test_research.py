"""Learning math, data leakage controls, reproducibility and application safety."""
import csv
import json
from pathlib import Path

import pytest

from analyze import run
from app import create_app
from chatbot.intent_model import IntentModel, clean_question, knowledge_fingerprint, load_model
from chatbot.retriever import retrieve
from research.dataset import load_dataset
from research.evaluation import classification_metrics

ROOT = Path(__file__).resolve().parents[1]


def test_naive_bayes_matches_hand_calculated_posterior():
    model = IntentModel.fit([{'faq_id': 'A', 'question': 'apple apple'}, {'faq_id': 'B', 'question': 'pear'}])
    ranked = model.predict('apple')
    # Equal priors; smoothed likelihoods 3/4 and 1/3 yield posterior 9/13.
    assert ranked[0]['faq_id'] == 'A'
    assert ranked[0]['score'] == pytest.approx(9 / 13)
    assert sum(item['score'] for item in ranked) == pytest.approx(1)
    assert model.predict('unseenword') == []


def test_bigrams_capture_order_while_unigrams_do_not():
    rows = [{'faq_id': 'A', 'question': 'blue red'}, {'faq_id': 'B', 'question': 'red blue'}]
    assert IntentModel.fit(rows).predict('red blue')[0]['score'] == pytest.approx(.5)
    assert IntentModel.fit(rows, ngram_max=2).predict('red blue')[0]['faq_id'] == 'B'


@pytest.mark.parametrize('alpha', [0, -1, float('nan'), float('inf')])
def test_invalid_smoothing_is_rejected(alpha):
    with pytest.raises(ValueError):
        IntentModel.fit([{'faq_id': 'A', 'question': 'apple'}, {'faq_id': 'B', 'question': 'pear'}], alpha=alpha)


def test_normalization_preserves_negation_and_program_tokens():
    assert clean_question('  ＢＳＣＳ   ISN’T   online  ') == "bscs isn't online"


def write_dataset(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['sample_id', 'question', 'faq_id', 'split', 'language', 'provenance'])
        writer.writeheader()
        writer.writerows(rows)


def base_rows():
    return [dict(sample_id=f'{label}-{split}', question=f'{label} {split} question', faq_id=label,
                 split=split, language='English', provenance='Synthetic unit-test fixture')
            for label in ['A', 'B'] for split in ['train', 'validation', 'test']]


def test_csv_reports_actual_cleaning_and_keeps_valid_long_questions(tmp_path):
    rows = base_rows()
    rows[0]['question'] = ' A   TRAIN question '
    rows.append({**rows[0], 'sample_id': 'duplicate'})
    rows.append({**rows[0], 'sample_id': 'missing', 'question': ''})
    rows.append({**rows[0], 'sample_id': 'invalid', 'question': 'x' * 1001})
    path = tmp_path / 'questions.csv'
    write_dataset(path, rows)
    cleaned, profile = load_dataset(path, {'A', 'B'})
    assert len(cleaned) == 6
    assert profile['quality']['duplicate_rows_removed'] == 1
    assert profile['quality']['missing_rows_removed'] == 1
    assert profile['quality']['invalid_rows_removed'] == 1
    assert cleaned[0]['question'] == 'a train question'


@pytest.mark.parametrize('changed', [
    {'split': 'validation'}, {'faq_id': 'B'},
])
def test_cross_split_duplicates_and_label_conflicts_stop_training(tmp_path, changed):
    rows = base_rows()
    rows.append({**rows[0], 'sample_id': 'bad-copy', **changed})
    path = tmp_path / 'questions.csv'
    write_dataset(path, rows)
    with pytest.raises(ValueError, match='leakage|Conflicting'):
        load_dataset(path, {'A', 'B'})


def test_unknown_labels_cannot_become_department_answers(tmp_path):
    path = tmp_path / 'questions.csv'
    write_dataset(path, base_rows())
    with pytest.raises(ValueError, match='Unknown FAQ'):
        load_dataset(path, {'A'})


def test_missing_class_in_test_split_is_rejected(tmp_path):
    path = tmp_path / 'questions.csv'
    write_dataset(path, base_rows()[:-1])
    with pytest.raises(ValueError, match='test split'):
        load_dataset(path, {'A', 'B'})


def test_metrics_account_for_false_positives_and_abstentions():
    metrics = classification_metrics(['A', 'A', 'B', 'B'], ['A', 'B', 'B', 'ABSTAIN'], ['A', 'B'])
    assert metrics['accuracy'] == .5
    assert metrics['macro_precision'] == .75
    assert metrics['macro_recall'] == .5
    assert metrics['macro_f1'] == pytest.approx((2 / 3 + .5) / 2)
    assert sum(map(sum, metrics['confusion_matrix'])) == 4


def test_artifact_fingerprint_prevents_stale_models(tmp_path):
    records = [{'id': 'A', 'question': 'apple', 'answer': 'Apple'}, {'id': 'B', 'question': 'pear', 'answer': 'Pear'}]
    model = IntentModel.fit([{'faq_id': r['id'], 'question': r['question']} for r in records],
                            metadata={'knowledge_sha256': knowledge_fingerprint(records)})
    path = tmp_path / 'model.json'
    model.save(path)
    assert load_model(path, records) is not None
    original = json.loads(path.read_text())
    for invalid in ({**original, 'class_counts': []}, {**original, 'term_counts': {'A': []}},
                    {**original, 'class_counts': {'A': -1, 'B': 1}}):
        path.write_text(json.dumps(invalid))
        assert load_model(path, records) is None
    model.save(path)
    records[0]['answer'] = 'Changed source'
    assert load_model(path, records) is None
    path.write_text('{invalid json')
    assert load_model(path, records) is None


def test_model_scores_cannot_override_source_detail_guards():
    class AlwaysFacilities:
        def predict(self, question):
            return [{'faq_id': 'TEST', 'score': 1}]
    records = [{'id': 'TEST', 'category': 'facilities', 'question': 'What laboratories are available?',
                'answer': 'The AI Laboratory is available.', 'keywords': ['labs'], 'verification_status': 'verified'}]
    assert retrieve('What labs are available?', records, AlwaysFacilities())
    assert retrieve('What time do the labs open?', records, AlwaysFacilities()) == []


def test_training_reproduces_published_results_without_test_vocabulary(tmp_path):
    report = run(ROOT / 'data/question_dataset.csv', tmp_path, make_figures=False)
    published = json.loads((ROOT / 'research/results/report.json').read_text())
    assert report['experiments'] == published['experiments']
    assert report['test'] == published['test']
    artifact = json.loads((tmp_path / 'model.json').read_text())
    assert len(artifact['metadata']['training_sample_ids']) == 176
    assert all(not sample.endswith(('Q09', 'Q10', 'Q11', 'Q12')) for sample in artifact['metadata']['training_sample_ids'])
    assert sum(artifact['class_counts'].values()) == 176
    # This token occurs in a held-out question but not in training.
    assert 'initials' not in artifact['vocabulary']


@pytest.fixture
def client():
    return create_app({'TESTING': True, 'CHAT_MODE': 'faq', 'API_KEY': None}).test_client()


def test_analysis_and_prediction_work_without_any_ai_key(client):
    assert client.get('/api/health').get_json()['intent_model_ready']
    assert client.get('/analysis').status_code == 200
    data = client.get('/api/analysis').get_json()['report']
    assert data['dataset']['quality']['retained_rows'] == 264
    predicted = client.post('/api/classify', json={'message': 'Who teaches BSCS?'}).get_json()
    assert predicted['predictions'][0]['faq_id'] == 'FAQ-018'
    assert 'uncalibrated' in predicted['note']
    assert client.get('/analysis/figures/class_distribution.png').status_code == 200
    assert client.get('/analysis/figures/model.json').status_code == 404


def test_analysis_has_a_clear_missing_artifact_state(tmp_path):
    client = create_app({'TESTING': True, 'ANALYSIS_ROOT': tmp_path}).test_client()
    assert client.get('/analysis').status_code == 200
    assert client.get('/api/analysis').status_code == 503
    assert client.post('/api/classify', json={'message': 'Who teaches BSCS?'}).status_code == 503


@pytest.mark.parametrize('body', [None, [], {'message': ''}, {'message': 'x' * 1001}, {'message': 'Show my student grades'}])
def test_prediction_validates_input_and_private_record_requests(client, body):
    assert client.post('/api/classify', json=body).status_code == 400
