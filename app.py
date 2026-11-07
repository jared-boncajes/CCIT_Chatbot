import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from chatbot.retriever import retrieve
from chatbot.ai_service import DEFAULT_MODELS, generate

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')
FALLBACK = "I don't currently have verified information about that. Please contact the CCIT department office for assistance."

# Titles and descriptions come from the revised Figma frame. Question choices
# come only from the reviewed knowledge records, never from design sample text.
TOPICS = [
    {
        'id': 'academics',
        'title': 'Programs & Academics',
        'description': 'Explore CCIT programs, subjects, and academic requirements.',
        'categories': {'academic_programs', 'bsit', 'bscs', 'bsemc', 'accreditation', 'careers'},
        'note': 'Choose a question from the department document. Subjects and detailed academic requirements are not documented yet.',
    },
    {
        'id': 'services',
        'title': 'Student Services',
        'description': 'Find information on enrollment, forms, and department procedures.',
        'categories': {'scholarships', 'dost', 'activities'},
        'note': 'The document covers scholarships, DOST scholarship acceptance, and student activities. Enrollment forms and procedures are not documented yet.',
    },
    {
        'id': 'directory',
        'title': 'Department Directory',
        'description': 'Find faculty contacts, offices, and facilities.',
        'categories': {'dean', 'faculty', 'facilities'},
        'note': 'The document lists the dean, faculty, and facilities. Contact details and office locations are not documented yet; current assignments need confirmation.',
    },
]

def create_app(test_config=None):
    app = Flask(__name__)
    provider = os.getenv('CCIT_AI_PROVIDER', 'openai').strip().lower()
    key_names = {
        'openai': ('CCIT_API_KEY', 'OPENAI_API_KEY'),
        'gemini': ('GEMINI_API_KEY', 'GOOGLE_API_KEY'),
    }.get(provider, ())
    app.config.update(MAX_CONTENT_LENGTH=16384, CHAT_MODE=os.getenv('CHAT_MODE','ai'),
        AI_PROVIDER=provider,
        API_KEY=next((os.getenv(name) for name in key_names if os.getenv(name)), None),
        MODEL=os.getenv('CCIT_MODEL') or DEFAULT_MODELS.get(provider, ''),
        KNOWLEDGE=json.loads((ROOT/'data/knowledge.json').read_text()))
    if test_config:
        app.config.update(test_config)

    @app.get('/')
    def index():
        return render_template('index.html', topics=TOPICS)

    @app.get('/api/health')
    def health():
        records=app.config['KNOWLEDGE']
        count=sum(r.get('verification_status')=='verified' for r in records)
        ai_configured = bool(app.config['AI_PROVIDER'] in DEFAULT_MODELS and app.config['API_KEY'])
        ready=bool(count and (app.config['CHAT_MODE']=='faq' or (app.config['CHAT_MODE']=='ai' and ai_configured)))
        return jsonify(success=True, ready=ready, mode=app.config['CHAT_MODE'],
            knowledge_records=len(records), verified_records=count,
            ai_configured=ai_configured, provider=app.config['AI_PROVIDER'])

    @app.get('/api/suggestions')
    def suggestions():
        reviewed = [r for r in app.config['KNOWLEDGE'] if r.get('verification_status') == 'verified']
        topics = [
            {
                'id': topic['id'],
                'title': topic['title'],
                'note': topic['note'],
                'questions': [r['question'] for r in reviewed if r.get('category') in topic['categories']],
            }
            for topic in TOPICS
        ]
        return jsonify(success=True, questions=[r['question'] for r in reviewed][:6], topics=topics)

    @app.post('/api/chat')
    def chat():
        body=request.get_json(silent=True)
        message=body.get('message') if isinstance(body,dict) else None
        if not isinstance(message,str) or not message.strip() or len(message)>1000:
            return jsonify(success=False,error='Enter a question between 1 and 1,000 characters.'),400
        message=message.strip()
        if re.search(r'\b(my|his|her|student|aking)\b.*\b(grades?|records?|password|address)\b',message,re.I):
            return jsonify(success=True,reply='I cannot access private student records. Please use the official student services channels.',sources=[],mode='privacy')
        if not app.config['KNOWLEDGE']:
            return jsonify(success=False,error='The About CCIT knowledge document has not been imported yet. Department answers are unavailable.'),503
        if app.config['CHAT_MODE'] not in ('ai','faq'):
            return jsonify(success=False,error='The chatbot mode is not configured correctly.'),503
        if app.config['CHAT_MODE']=='ai' and app.config['AI_PROVIDER'] not in DEFAULT_MODELS:
            return jsonify(success=False,error='Set CCIT_AI_PROVIDER to gemini or openai in the backend configuration.'),503
        if app.config['CHAT_MODE']=='ai' and not app.config['API_KEY']:
            key_name = 'GEMINI_API_KEY' if app.config['AI_PROVIDER']=='gemini' else 'CCIT_API_KEY'
            return jsonify(success=False,error=f'AI service is not configured. Add {key_name} to the backend .env file or environment settings, then restart the server. FAQ mode is also available.'),503
        records=retrieve(message, app.config['KNOWLEDGE'])
        if not records:
            return jsonify(success=True,reply=FALLBACK,sources=[],mode='fallback')
        try:
            reply='\n\n'.join(r['answer'] for r in records) if app.config['CHAT_MODE']=='faq' else generate(message,records,app.config['API_KEY'],app.config['MODEL'],app.config['AI_PROVIDER'])
        except Exception:
            app.logger.warning('AI response unavailable')
            return jsonify(success=False,error='The AI service is unavailable. Please try again shortly.'),502
        if any(r.get('currency_status') == 'unconfirmed' for r in records):
            reply = 'According to the supplied About CCIT document (current details have not been independently confirmed):\n\n' + reply
        if any(r['id'] in ('FAQ-001','FAQ-002') for r in records):
            reply += '\n\nSource note: the document uses both “College of Computer” and “College of Computing” in the college name. Please confirm the official wording with CCIT.'
        return jsonify(success=True,reply=reply,mode=app.config['CHAT_MODE'],sources=[{'id':r['id'],'title':r['question'],'source':r.get('source','About CCIT')} for r in records])

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(success=False,error=error.description),error.code
    return app

app=create_app()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=False)
