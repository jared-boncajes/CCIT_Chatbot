"""Representative abbreviations and named roster answers must stay scoped."""
import pytest

from app import create_app
from chatbot.retriever import tokens


@pytest.fixture
def client():
    return create_app({'TESTING': True, 'CHAT_MODE': 'faq'}).test_client()


@pytest.mark.parametrize('question', [
    'Who are the CS Representatives', 'Who are the BSCS representatives',
    'CS reps', 'CS rep', 'Computer Science reps',
])
def test_program_representatives_use_named_roster(client, question):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert [s['id'] for s in data['sources']] == ['FAQ-186']
    for name in ('Voltaire Jan O. Punzalan', 'Neil Allen P. Morte', 'Dominic G. Gutierrez', 'Karyl Fay V. Santiago'):
        assert name in data['reply']
    assert 'Melanie A. Perez' not in data['reply']
    assert '2025-2026' in data['reply']


@pytest.mark.parametrize('question', ['Who is the 2nd year BSCS representative?', '2nd yr CS reps', 'CS2 reps', 'CS 2nd reps'])
def test_year_specific_reps(client, question):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert 'Dominic G. Gutierrez' in data['reply']
    assert 'Karyl Fay' not in data['reply'] and 'Voltaire' not in data['reply']
    assert data['sources'][0]['id'] == 'FAQ-186'


@pytest.mark.parametrize('question,names', [
    ('BSIT 3A reps', ['Naika Ishi D. Gumila']),
    ('IT 3rd yr reps', ['Naika Ishi D. Gumila', 'Jose Eugenio P. Platero']),
    ('BSEMC sophomore reps', ['Cristine Mae S. Elcarte']),
    ('it 3A reps', ['Naika Ishi D. Gumila']),
])
def test_sections_and_other_programs(client, question, names):
    data = client.post('/api/chat', json={'message': question}).get_json()
    for name in names:
        assert name in data['reply']
    if '3A' in question:
        assert 'Jose Eugenio' not in data['reply']


@pytest.mark.parametrize('question', ['BSCS fifth year reps', 'BSCS 5 reps', 'BSIT 3C reps', 'BSN reps', 'CS reps for 2027-2028'])
def test_unknown_representative_scope_does_not_guess(client, question):
    data = client.post('/api/chat', json={'message': question}).get_json()
    assert data['mode'] == 'fallback' and data['sources'] == []


def test_representative_year_clarification_and_followup(client):
    first = client.post('/api/chat', json={'message': '2nd year reps'}).get_json()
    assert first['mode'] == 'clarification'
    final = client.post('/api/chat', json={'message': 'CS', 'context': first['context']}).get_json()
    assert 'Dominic G. Gutierrez' in final['reply']
    broader = client.post('/api/chat', json={'message': 'CS reps'}).get_json()
    followup = client.post('/api/chat', json={'message': 'and 2nd year?', 'context': broader['context']}).get_json()
    assert 'Dominic G. Gutierrez' in followup['reply']
    assert 'Voltaire' not in followup['reply']


def test_ai_receives_only_the_requested_names(client, monkeypatch):
    client.application.config.update(CHAT_MODE='ai', API_KEY='synthetic-test-key')
    def generate(question, records, *args):
        assert len(records) == 1 and records[0]['id'] == 'FAQ-186'
        assert 'Dominic G. Gutierrez' in records[0]['answer']
        assert 'Karyl Fay' not in records[0]['answer']
        assert '2025-2026' in records[0]['answer']
        return records[0]['answer']
    monkeypatch.setattr('app.generate', generate)
    data = client.post('/api/chat', json={'message': 'CS 2nd year reps'}).get_json()
    assert data['mode'] == 'ai'
    assert 'Karyl Fay' in data['details'][0]['answer']  # Full source kept for audit.


@pytest.mark.parametrize('short,long', [('reps','representatives'),('rep','representatives'),('prereqs','prerequisites'),('pre-reqs','prerequisites'),('coreqs','corequisites'),('orgs','organizations'),('profs','faculty'),('subjs','subjects'),('yr','year')])
def test_abbreviations(short, long):
    assert tokens(short) == tokens(long)
