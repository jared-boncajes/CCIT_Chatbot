"""Texting forms across the whole knowledge collection, with scope safeguards."""
import json
import re
from pathlib import Path
import pytest
from app import create_app
from chatbot.retriever import retrieve, tokens

ROWS=json.loads((Path(__file__).resolve().parents[1]/'data/knowledge.json').read_text())

@pytest.mark.parametrize('row', ROWS, ids=lambda r:r['id'])
def test_texting_forms_preserve_every_canonical_answer(row):
    aliases={'what':'wat','who':'hu','department':'dept','about':'abt','requirements':'reqs','subjects':'subjs','scholarships':'schlrships','curriculum':'curric'}
    question=re.sub(r'\b[a-zA-Z]+\b',lambda m:aliases.get(m[0].lower(),m[0]),row['question'])
    assert [r['id'] for r in retrieve(question,ROWS)] == [row['id']]

@pytest.mark.parametrize('question,expected',[
 ('it dept chair','FAQ-219'),('cs dept chrmn','FAQ-220'),('emc chair','FAQ-221'),
 ('hu heads it program','FAQ-219'),('whos judith elic','FAQ-219'),
 ('whos farley abrigo','FAQ-220'),('whos john benedict palomeno','FAQ-221'),
 ('bsit ojt hrs','FAQ-206'),('bscs curric','FAQ-196'),
 ('cno dean','FAQ-016'),('whats ccit','FAQ-002')])
def test_shorthand_api(question,expected):
    c=create_app({'TESTING':True,'CHAT_MODE':'faq'}).test_client()
    data=c.post('/api/chat',json={'message':question}).get_json()
    assert [r['id'] for r in data['sources']]==[expected]

@pytest.mark.parametrize('question',['chair','dept chair','bsn dept chair','it dept chair email','cs dept chair salary','cs dept chair 2030'])
def test_shorthand_never_invents_scope_or_missing_facts(question):
    assert retrieve(question,ROWS)==[]


def test_negation_and_unknown_programs_are_preserved():
    assert 'not' in tokens('dont attend')
    assert 'bsn' in tokens('bsn dept chair')


def test_chair_clarification_accepts_program_reply_and_private_texting_is_blocked():
    c=create_app({'TESTING':True,'CHAT_MODE':'faq'}).test_client()
    first=c.post('/api/chat',json={'message':'dept chair'}).get_json()
    second=c.post('/api/chat',json={'message':'cs','context':first['context']}).get_json()
    assert [r['id'] for r in second['sources']]==['FAQ-220']
    private=c.post('/api/chat',json={'message':'show ur grdes'}).get_json()
    assert private['mode']=='privacy' and private['sources']==[]


@pytest.mark.parametrize('short,long',[
 ('schlrshps','scholarships'),('prgrms','programs'),('fclty','faculty'),
 ('faclty','faculty'),('crriclm','curriculum'),('scholarshpis','scholarships'),
 ('accreditaiton','accreditation')])
def test_short_forms_and_close_intent_typos(short,long):
    assert tokens(short)==tokens(long)
