"""Underspecified requests must not turn into arbitrary source-backed answers."""
import pytest

from app import create_app
from chatbot.retriever import retrieve


@pytest.fixture
def client():
    return create_app({'TESTING': True, 'CHAT_MODE': 'faq'}).test_client()


@pytest.mark.parametrize('question', [
    'prerequisites', 'prerequisite', 'prereq', 'prerequsites', 'co-requisites',
    'BSCS prerequisites', 'What are the prerequisite requirements?',
    'ITECC03 prerequisites', 'Computer Programming 2 prerequisites',
    'BSIT subjects', 'subjects', 'first year subjects', 'curriculum',
    'OJT', 'OJT hours', 'requirements', 'hours', 'contact', 'schedule',
    'What subjects are in BSCS?', 'What subjects are in BSEMC?',
    'ITECC03', 'GEWORLD', 'BSIT ITECC03', 'community service',
])
def test_broad_requests_ask_before_retrieval_or_generation(client, monkeypatch, question):
    def unexpected(*args):
        raise AssertionError('An ambiguous request must not call AI or classifier ranking')
    monkeypatch.setattr('app.generate', unexpected)
    monkeypatch.setattr(client.application.config['INTENT_MODEL'], 'predict', unexpected)
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['mode'] == 'clarification'
    assert data['sources'] == []
    assert data['reply'].endswith(('?', '.'))
    assert retrieve(question, client.application.config['KNOWLEDGE']) == []


@pytest.mark.parametrize('turns,expected', [
    (['prerequisites', 'ITECC03', 'BSCS'], 'FAQ-030'),
    (['prerequisites', 'Computer Programming 2', 'BSIT'], 'FAQ-081'),
    (['BSIT prerequisites', 'ITECC03'], 'FAQ-081'),
    (['prerequisites', 'GEWORLD', 'BSCS'], 'FAQ-034'),
    (['subjects', 'BSIT', 'second'], 'FAQ-193'),
    (['first year subjects', 'BSCS'], 'FAQ-197'),
    (['BSIT subjects', '2'], 'FAQ-193'),
    (['OJT', 'BSCS'], 'FAQ-207'),
])
def test_clarification_collects_selectors_across_turns(client, turns, expected):
    context = {'programs': []}
    for index, question in enumerate(turns):
        data = client.post('/api/chat', json={'message': question, 'context': context}).get_json()
        context = data['context']
        if index < len(turns) - 1:
            assert data['mode'] == 'clarification', data
            assert data['sources'] == []
    assert data['mode'] == 'faq', data
    assert [r['id'] for r in data['sources']] == [expected]
    assert 'pending_topic' not in context


@pytest.mark.parametrize('question', [
    'Prerequisites of ITECC99 in BSCS', 'ITECC03 prerequisites in BSN',
    'ITECC03 and ITECC99 prerequisites BSCS', 'BSIT fifth year curriculum',
    'FREEHDD prerequisites BSCS',
])
def test_unknown_or_wrong_scope_does_not_fuzzy_match(client, question):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['mode'] == 'fallback'
    assert data['sources'] == []


@pytest.mark.parametrize('question,expected', [
    ('BSIT curriculum', 'FAQ-191'), ('BSCS OJT hours', 'FAQ-207'),
    ('events', 'FAQ-210'), ('FACTS', 'FAQ-180'),
    ('Prerequisites of Programming 2 in BSCS', 'FAQ-030'),
    ('How does FAITH help find OJT companies?', 'FAQ-209'),
])
def test_specific_requests_and_overviews_still_work(client, question, expected):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['mode'] == 'faq', data
    assert [r['id'] for r in data['sources']] == [expected]


def test_new_topic_discards_pending_subject(client):
    first = client.post('/api/chat', json={'message': 'ITECC03 prerequisites'}).get_json()
    switched = client.post('/api/chat', json={'message': 'Who is the dean?', 'context': first['context']}).get_json()
    assert switched['sources'][0]['id'] == 'FAQ-016'
    assert 'pending_topic' not in switched['context']


def test_replacing_subject_does_not_reuse_old_subject(client):
    first = client.post('/api/chat', json={'message': 'ITECC03 prerequisites'}).get_json()
    changed = client.post('/api/chat', json={'message': 'Computer Programming 1', 'context': first['context']}).get_json()
    assert changed['context']['pending_subject'] == 'ITECC02'


@pytest.mark.parametrize('context', [
    {'programs': [], 'pending_topic': 'prerequisites', 'pending_subject': 'x' * 100},
    {'programs': [], 'pending_topic': 'curriculum', 'pending_year': True},
    {'programs': [], 'pending_topic': 'curriculum', 'pending_year': 99},
    {'programs': [], 'pending_subject': 'ITECC03'},
])
def test_pending_selectors_are_validated(client, context):
    assert client.post('/api/chat', json={'message': 'BSCS', 'context': context}).status_code == 400


def test_ai_mode_also_clarifies_without_calling_provider(client, monkeypatch):
    client.application.config.update(CHAT_MODE='ai', API_KEY='synthetic-test-key')
    def unexpected(*args):
        raise AssertionError('Clarification must happen before generation')
    monkeypatch.setattr('app.generate', unexpected)
    data = client.post('/api/chat', json={'message': 'prerequisites'}).get_json()
    assert data['mode'] == 'clarification' and data['sources'] == []


def test_program_from_previous_turn_does_not_supply_a_subject(client):
    first = client.post('/api/chat', json={'message': 'What is BSIT?'}).get_json()
    broad = client.post('/api/chat', json={'message': 'prerequisites', 'context': first['context']}).get_json()
    assert broad['mode'] == 'clarification' and not broad['sources']
    specific = client.post('/api/chat', json={'message': 'ITECC03', 'context': broad['context']}).get_json()
    assert specific['sources'][0]['id'] == 'FAQ-081'


@pytest.mark.parametrize('turns,mode,expected', [
    (['contact', 'FACTS'], 'faq', 'FAQ-188'),
    (['schedule', 'CCIT Camp'], 'fallback', None),
    (['hours', 'OJT', 'BSCS'], 'faq', 'FAQ-207'),
    (['community service', 'render'], 'faq', 'FAQ-218'),
])
def test_generic_clarification_keeps_the_requested_detail(client, turns, mode, expected):
    context = {'programs': []}
    for question in turns:
        data = client.post('/api/chat', json={'message': question, 'context': context}).get_json()
        context = data['context']
    assert data['mode'] == mode
    assert [r['id'] for r in data['sources']] == ([expected] if expected else [])
