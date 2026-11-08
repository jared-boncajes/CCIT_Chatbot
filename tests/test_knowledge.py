import json
from pathlib import Path
import pytest
from app import create_app

CASES=[
('What is the meaning of CCIT?','FAQ-001'),('What is CCIT all about?','FAQ-002'),
('What is the vision?','FAQ-003'),('MISSION','FAQ-004'),('What are the goals?','FAQ-005'),
('What programs are available?','FAQ-006'),('Ano mga kurso sa CCIT?','FAQ-006'),
('courses','FAQ-006'),('What graduate degrees are available?','FAQ-006'),
('What is BSIT?','FAQ-007'),('What is Computer Science?','FAQ-008'),
('What is BSEMC?','FAQ-009'),('Does CCIT have academic accreditation?','FAQ-010'),
('PACUCOA accreditation','FAQ-010'),('Does CCIT offer scholarships?','FAQ-012'),
('50-TAG tuition discount','FAQ-012'),('What careers after BSCS?','FAQ-013'),
('BSIT jobs','FAQ-014'),('BSEMC careers','FAQ-015'),('Who is the dean?','FAQ-016'),
('Sino ang dean?','FAQ-016'),('BSIT faculty','FAQ-017'),('Computer Science teachers','FAQ-018'),
('BSEMC faculty members','FAQ-019'),('What facilities are available?','FAQ-189'),
('laboratories','FAQ-189'),('DOST scholarships','FAQ-021'),('non-academic activities','FAQ-022'),
('What is the misson?','FAQ-004'),('What are my grades?','privacy'),
('When is tomorrow meeting?','fallback'),('How do I bake bread?','fallback'),
('What is the tuition amount?','fallback'),('What is the dean phone number?','fallback')]
@pytest.mark.parametrize('question,expected',CASES)
def test_source_retrieval(question,expected):
    client=create_app({'TESTING':True,'CHAT_MODE':'faq'}).test_client()
    data=client.post('/api/chat',json={'message':question}).get_json()
    if expected in ('privacy','fallback'):
        assert data['mode']==expected
    else:
        assert data['sources'][0]['id']==expected
