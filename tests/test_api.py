import pytest
from app import create_app

# Deliberately synthetic fixtures: these are not department knowledge.
RECORD={'id':'TEST-1','question':'What programs exist?','answer':'Synthetic test answer','keywords':['programs','courses'],'verification_status':'verified','source':'Test fixture'}
@pytest.fixture
def client():
    return create_app({'TESTING':True,'CHAT_MODE':'faq','KNOWLEDGE':[RECORD],'API_KEY':None}).test_client()
@pytest.mark.parametrize('body',[{},[],None,{'message':''},{'message':' '},{'message':7},{'message':'x'*1001}])
def test_invalid(client,body):
    assert client.post('/api/chat',json=body).status_code==400
@pytest.mark.parametrize('question',['What programs exist?','courses','PROGRAMS','Ano mga kurso sa CCIT?','programms'])
def test_retrieval(client,question):
    data=client.post('/api/chat',json={'message':question}).get_json()
    assert data['reply']=='Synthetic test answer'
    assert data['mode']=='faq' and data['sources'][0]['id']=='TEST-1'
def test_unknown(client):
    data=client.post('/api/chat',json={'message':'Tomorrow meeting deadline'}).get_json()
    assert not data['sources'] and data['mode']=='fallback'
def test_private(client):
    assert 'cannot access' in client.post('/api/chat',json={'message':'What are my grades?'}).get_json()['reply']
def test_no_data():
    client=create_app({'TESTING':True,'KNOWLEDGE':[]}).test_client()
    assert client.post('/api/chat',json={'message':'courses'}).status_code==503
    assert not client.get('/api/health').get_json()['ready']
def test_unreviewed(client):
    client.application.config['KNOWLEDGE']=[{**RECORD,'verification_status':'pending'}]
    assert not client.post('/api/chat',json={'message':'courses'}).get_json()['sources']
def test_missing_key(client):
    client.application.config['CHAT_MODE']='ai'
    assert client.post('/api/chat',json={'message':'courses'}).status_code==503
def test_provider_error(client,monkeypatch):
    client.application.config.update(CHAT_MODE='ai',API_KEY='test-fixture')
    def fail(*args): raise TimeoutError('sensitive test detail')
    monkeypatch.setattr('app.generate',fail)
    response=client.post('/api/chat',json={'message':'courses'})
    assert response.status_code==502 and b'sensitive' not in response.data

def test_frontend(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Ask CCIThink' in response.data
    assert b'Programs &amp; Academics' in response.data
    assert client.get('/static/js/script.js').status_code==200


def test_topics_use_reviewed_source_questions(client):
    client.application.config['KNOWLEDGE'] = [
        {**RECORD, 'id': 'PROGRAMS', 'category': 'academic_programs'},
        {**RECORD, 'id': 'FACULTY', 'question': 'Faculty fixture?', 'category': 'faculty'},
        {**RECORD, 'id': 'PENDING', 'question': 'Unreviewed fixture?', 'category': 'scholarships', 'verification_status': 'pending'},
    ]
    data = client.get('/api/suggestions').get_json()
    topics = {topic['id']: topic for topic in data['topics']}
    assert topics['academics']['questions'] == [RECORD['question']]
    assert topics['directory']['questions'] == ['Faculty fixture?']
    assert topics['services']['questions'] == []
    assert 'Unreviewed fixture?' not in data['questions']
