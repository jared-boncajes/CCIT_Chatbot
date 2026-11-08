"""Import integrity and retrieval of the expanded, user-supplied knowledge."""
import json
from collections import Counter
from pathlib import Path

import pytest

from app import create_app
from chatbot.intent_model import load_model
from chatbot.retriever import normalize, retrieve

ROWS = json.loads((Path(__file__).resolve().parents[1] / 'data/knowledge.json').read_text())


def test_database_integrity():
    assert len(ROWS) == 221
    assert len({row['id'] for row in ROWS}) == 221
    assert {row['source_id'] for row in ROWS} == set(range(1, 222))
    source = json.loads((Path(__file__).resolve().parents[1] / 'data/sources/database_v3.json').read_text())
    by_id = {r['id']: r for r in source}
    for row in ROWS:
        original = by_id[row['source_id']]
        for field in ('question', 'answer', 'alternative_questions', 'keywords'):
            assert row[field] == original[field]
        assert row['source_category'] == original['category']
        assert row['question'].strip() and row['answer'].strip()
        assert row['source'] == 'database_v3.json'
        assert row['currency_status'] == 'unconfirmed'
        assert all(isinstance(q, str) and q.strip() for q in row['alternative_questions'])


@pytest.mark.parametrize('row', ROWS, ids=lambda row: row['id'])
def test_every_canonical_question_retrieves_its_record(row):
    assert [r['id'] for r in retrieve(row['question'], ROWS)] == [row['id']]


@pytest.mark.parametrize('program,expected', [('BSCS', 'FAQ-030'), ('BSIT', 'FAQ-081'), ('BSEMC-DA', 'FAQ-132')])
def test_shared_course_code_is_scoped_to_its_program(program, expected):
    results = retrieve(f'ITECC03 prerequisite {program}', ROWS)
    assert [r['id'] for r in results] == [expected]


def test_unknown_course_does_not_return_a_similar_code():
    assert retrieve('Prerequisite of ITECC99 in BSCS', ROWS) == []


@pytest.mark.parametrize('faq_id', ['FAQ-055', 'FAQ-186', 'FAQ-192', 'FAQ-207', 'FAQ-218'])
def test_expanded_answers_are_complete_through_api(faq_id):
    row = next(r for r in ROWS if r['id'] == faq_id)
    client = create_app({'TESTING': True, 'CHAT_MODE': 'faq'}).test_client()
    data = client.post('/api/chat', json={'message': row['question']}).get_json()
    assert data['sources'][0]['id'] == faq_id
    assert data['details'][0]['answer'] == row['answer']
    assert data['reply'] == row['answer']
    assert data['sources'][0]['source'] == 'database_v3.json'


def test_stale_classifier_is_not_loaded():
    legacy = Path(__file__).resolve().parents[1] / 'research/results/model.json'
    assert load_model(legacy, ROWS) is None


def test_alternative_questions_retrieve_the_authored_record_or_request_missing_year():
    def key(q):
        return normalize(q).strip(' ?.\n')
    canonical = {key(r['question']): r['id'] for r in ROWS}
    counts = Counter(key(q) for r in ROWS for q in r['alternative_questions'])
    checked = 0
    for row in ROWS:
        for question in row['alternative_questions']:
            query = key(question)
            if counts[query] > 1 and query not in canonical:
                continue  # Shared variants do not establish a unique target.
            expected = canonical.get(query, row['id'])
            if question in {'What subjects are in BSCS?', 'What subjects are in BSEMC?'}:
                # These supplied aliases omit the year needed for a subject
                # list. Do not let exact matching bypass scope clarification.
                from chatbot.scope import scope_candidates
                assert retrieve(question, ROWS) == []
                assert 'year level' in scope_candidates(question, ROWS)[1]
            else:
                assert [r['id'] for r in retrieve(question, ROWS)] == [expected]
            checked += 1
    assert checked == 726
