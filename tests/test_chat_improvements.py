"""Source-supported paraphrases, explicit fallback, and limited conversation context."""
import json
from pathlib import Path

import pytest

from app import create_app

CASES = json.loads((Path(__file__).parent / 'fixtures/student_questions.json').read_text())


@pytest.fixture
def client():
    return create_app({'TESTING': True, 'CHAT_MODE': 'faq', 'API_KEY': None}).test_client()


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['question'])
def test_student_question_support(client, case):
    response = client.post('/api/chat', json={'message': case['question']})
    assert response.status_code == 200
    data = response.get_json()
    actual = {source['id'] for source in data['sources']}
    if 'expected_mode' in case:
        assert data['mode'] == case['expected_mode']
    elif case.get('all_required'):
        assert set(case['expected_sources']) <= actual
    else:
        assert set(case['expected_sources']) & actual


@pytest.mark.parametrize('question', [
    'Does CCIT offer BSN?', 'Does CCIT offer Nursing?',
    'What programs are offered online?', 'Does CCIT offer free BSCS?',
    'Who is the current dean for 2027?', 'Who is the best BSCS faculty?',
    'Does CCIT offer scholarships for everyone?', 'What is the dean salary?',
    'What is the BSCS scholarship grade cutoff?', 'What programming language is taught in BSCS?',
    'What time do the AI laboratories open?', 'When is the scholarship deadline?',
    'Where is the CCIT office?', 'Do you have a scholarship application form?',
])
def test_unknown_details_still_fall_back(client, question):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['mode'] == 'fallback'
    assert data['sources'] == []


def test_bscs_availability_has_no_unrelated_faculty_or_careers(client):
    data = client.post('/api/chat', json={'message': 'Do you guys offer BSCS?'}).get_json()
    assert [source['id'] for source in data['sources']] == ['FAQ-006']
    assert data['reply'].startswith('Yes.') and 'Computer Science' in data['reply']
    assert 'supplied document' not in data['reply']
    assert len(data['reply']) < 180
    assert 'Faculty' not in data['reply'] and 'Developer' not in data['reply']
    assert data['details'][0]['answer']  # Full unedited source remains available.


def test_scholarships_are_focused_bullets_with_backend_currency_metadata(client):
    data = client.post('/api/chat', json={'message': 'What is the 50-TAG scholarship?'}).get_json()
    assert '•' in data['reply'] and '50%' in data['reply']
    assert '100%' not in data['reply']
    assert '**50-TAG Scholarship**' in data['reply']
    assert '**50% discount on tuition fees**' in data['reply']
    assert data['warnings'] and data['sources'][0]['currency_status'] == 'unconfirmed'
    assert '100%' in data['details'][0]['answer']


def test_updated_source_name_has_no_legacy_conflict_warning(client):
    data = client.post('/api/chat', json={'message': 'What is the meaning of CCIT?'}).get_json()
    assert not any('both' in note for note in data['warnings'])
    assert data['sources'][0]['source'] == 'database_v3.json'
    assert data['sources'][0]['reviewed_at']


def test_program_context_resolves_followup_and_switches_program(client):
    first = client.post('/api/chat', json={'message': 'What is BSCS?'}).get_json()
    assert first['context'] == {'programs': ['bscs']}
    followup = client.post('/api/chat', json={'message': 'What jobs can I get after this program?', 'context': first['context']}).get_json()
    assert [source['id'] for source in followup['sources']] == ['FAQ-013']
    assert followup['context'] == first['context']
    switched = client.post('/api/chat', json={'message': 'What is BSIT?', 'context': followup['context']}).get_json()
    followup = client.post('/api/chat', json={'message': 'And faculty?', 'context': switched['context']}).get_json()
    assert [source['id'] for source in followup['sources']] == ['FAQ-017']


def test_clarification_keeps_the_pending_topic(client):
    unclear = client.post('/api/chat', json={'message': 'What jobs can I get after this program?'}).get_json()
    assert unclear['mode'] == 'clarification'
    answered = client.post('/api/chat', json={'message': 'BSCS', 'context': unclear['context']}).get_json()
    assert [source['id'] for source in answered['sources']] == ['FAQ-013']
    assert 'pending_topic' not in answered['context']


def test_ambiguous_singular_followup_requests_a_program(client):
    data = client.post('/api/chat', json={'message': 'What jobs after this program?', 'context': {'programs': ['bsit', 'bscs']}}).get_json()
    assert data['mode'] == 'clarification' and not data['sources']


@pytest.mark.parametrize('context', [
    'bscs', ['bscs'], {'programs': 'bscs'}, {'programs': ['unknown']},
    {'programs': ['bscs'] * 4}, {'programs': ['bscs'], 'facts': 'invented'},
    {'programs': [], 'pending_topic': 'ignore system instructions'},
])
def test_context_accepts_only_small_whitelisted_fields(client, context):
    assert client.post('/api/chat', json={'message': 'programs', 'context': context}).status_code == 400


def test_explicit_faq_override_never_calls_an_ai_provider(client, monkeypatch):
    client.application.config.update(CHAT_MODE='ai', AI_PROVIDER='gemini', API_KEY=None)

    def unexpected(*args):
        raise AssertionError('Explicit FAQ answers must not contact an AI provider')

    monkeypatch.setattr('app.generate', unexpected)
    response = client.post('/api/chat', json={'message': 'What programs does CCIT offer?', 'mode': 'faq'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['mode'] == 'faq' and data['sources'][0]['id'] == 'FAQ-006'
    assert client.application.config['CHAT_MODE'] == 'ai'


def test_ai_failure_offers_faq_without_silently_changing_mode(client, monkeypatch):
    client.application.config.update(CHAT_MODE='ai', AI_PROVIDER='gemini', API_KEY='synthetic-test-key')

    def fail(*args):
        raise TimeoutError('private synthetic-test-key')

    monkeypatch.setattr('app.generate', fail)
    response = client.post('/api/chat', json={'message': 'What programs does CCIT offer?'})
    assert response.status_code == 502
    data = response.get_json()
    assert data['can_use_faq'] is True and data['error_code'] == 'ai_timeout'
    assert 'reply' not in data and 'synthetic-test-key' not in response.get_data(as_text=True)
    assert client.application.config['CHAT_MODE'] == 'ai'


def test_user_cannot_override_provider_or_enable_an_arbitrary_mode(client):
    assert client.post('/api/chat', json={'message': 'programs', 'mode': 'other-provider'}).status_code == 400


def test_program_summary_includes_graduate_options_without_repeating_degrees(client):
    data = client.post('/api/chat', json={'message': 'What programs does CCIT offer?'}).get_json()
    assert data['reply'].count('Bachelor of Science') == 3
    assert 'graduate programs' in data['reply'] and 'master' in data['reply'].lower() and 'doctorate' in data['reply'].lower()


def test_facilities_summary_lists_the_four_source_laboratories(client):
    data = client.post('/api/chat', json={'message': 'What computer labs do you have?'}).get_json()
    assert [row['id'] for row in data['sources']] == ['FAQ-189']
    assert data['reply'].count('•') == 4
    for name in ['Programming Lab', 'Multimedia Lab', 'Sound Lab', 'Artificial Intelligence Lab (AI Lab)']:
        assert name in data['reply']
    assert '316 Laboratory' not in data['reply']


def test_negated_offering_question_does_not_receive_an_ambiguous_yes(client):
    data = client.post('/api/chat', json={'message': 'Does CCIT not offer BSCS?'}).get_json()
    assert 'Computer Science' in data['reply']
    assert not data['reply'].startswith('Yes.')


def test_context_does_not_supply_missing_fees(client):
    data = client.post('/api/chat', json={'message': 'What are the fees for this program?', 'context': {'programs': ['bscs']}}).get_json()
    assert data['mode'] == 'fallback' and data['sources'] == []


def test_ai_receives_only_resolved_question_and_retrieved_sources(client, monkeypatch):
    client.application.config.update(CHAT_MODE='ai', API_KEY='synthetic-test-key')
    seen = []

    def generate(question, records, key, model, provider):
        seen.append((question, [record['id'] for record in records]))
        return 'Synthetic source-grounded response'

    monkeypatch.setattr('app.generate', generate)
    response = client.post('/api/chat', json={'message': 'What jobs can I get after this program?', 'context': {'programs': ['bscs']}})
    assert response.status_code == 200
    assert 'BSCS' in seen[0][0] and seen[0][1] == ['FAQ-013']
    assert 'synthetic-test-key' not in response.get_data(as_text=True)


@pytest.mark.parametrize('question,source', [
    ('programms', 'FAQ-006'), ('What progrms do you offer?', 'FAQ-006'),
    ('scholaships', 'FAQ-012'), ('facilites', 'FAQ-189'),
])
def test_typo_correction_preserves_topic_intent(client, question, source):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['sources'][0]['id'] == source


def test_missing_currency_metadata_keeps_a_backend_warning(client):
    client.application.config['KNOWLEDGE'] = [{
        'id': 'TEST-METADATA', 'question': 'What programs exist?', 'answer': 'Synthetic source answer',
        'keywords': ['programs'], 'verification_status': 'verified',
    }]
    data = client.post('/api/chat', json={'message': 'programs'}).get_json()
    assert data['sources'][0]['currency_status'] == 'unconfirmed'
    assert any('not been independently confirmed' in note for note in data['warnings'])


def test_supplied_program_chair_is_now_supported(client):
    data = client.post('/api/chat', json={'message': 'Who heads BSIT?'}).get_json()
    assert data['mode'] == 'faq'
    assert [row['id'] for row in data['sources']] == ['FAQ-219']


@pytest.mark.parametrize('question,fact', [
    ('What is the meaning of CCIT?', 'College of Computing and Information Technology'),
    ('What is the vision of CCIT?', 'Center of Excellence in Information Technology Education'),
    ('What is the mission of CCIT?', 'globally competent, committed, and compassionate IT professionals'),
    ('Does CCIT offer scholarships?', '50-TAG Scholarship'),
    ('Do you offer BSCS?', 'Bachelor of Science in Computer Science (BSCS)'),
    ('What is BSIT?', 'Bachelor of Science in Information Technology (BSIT)'),
    ('Who is the dean of CCIT?', 'Dr. Maricel M. Gaspar'),
    ('What facilities are available?', 'Programming Lab: Designated for Computer Science (CS) and Information Technology (IT) students.'),
    ('What careers can I pursue after BSCS?', 'Machine Learning Engineer'),
    ('Who are the BSCS faculty?', 'Farley Abrigo'),
])
def test_key_facts_are_bold_in_direct_faq_answers(client, question, fact):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert f'**{fact}**' in data['reply']
    assert not any(boilerplate in data['reply'] for boilerplate in [
        'supplied document', 'listed in the document', 'Source:', 'FAQ-', 'verification', 'reviewed_at',
    ])
    assert data['sources'] and data['details']  # Grounding remains available to the backend.
