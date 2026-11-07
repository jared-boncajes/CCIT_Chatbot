import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from chatbot.retriever import retrieve
from chatbot.ai_service import DEFAULT_MODELS, generate
from chatbot.errors import diagnose
from chatbot.answers import format_faq, source_metadata
from chatbot.conversation import is_private_question, read_context, resolve_question

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
        if body.get('mode') not in (None, 'faq'):
            return jsonify(success=False,error='The requested answer mode is not supported.'),400
        try:
            context = read_context(body.get('context'))
        except ValueError:
            return jsonify(success=False,error='The conversation context is not valid. Please start a new chat.'),400
        if is_private_question(message):
            return jsonify(success=True,reply='I cannot access private student records. Please use the official student services channels.',sources=[],mode='privacy',context=context)
        if re.fullmatch(r'(?:hi|hello|hey|kumusta|magandang araw|thanks|thank you|salamat)[ !.]*', message, re.I):
            return jsonify(success=True,reply='Hello! Ask me about CCIT programs, scholarships, faculty, or facilities.',sources=[],mode='greeting',context=context)
        if not app.config['KNOWLEDGE']:
            return jsonify(success=False,error='The About CCIT knowledge document has not been imported yet. Department answers are unavailable.'),503
        mode = body.get('mode') or app.config['CHAT_MODE']
        if mode not in ('ai','faq'):
            return jsonify(success=False,error='The chatbot mode is not configured correctly.'),503
        resolved, next_context, needs_program = resolve_question(message, context)
        if needs_program:
            return jsonify(success=True,reply='Which program do you mean: BSCS, BSIT, or BSEMC?',sources=[],mode='clarification',context=next_context)
        records=retrieve(resolved, app.config['KNOWLEDGE'])
        if not records:
            return jsonify(success=True,reply=FALLBACK,sources=[],mode='fallback',context=next_context)
        if mode=='ai' and app.config['AI_PROVIDER'] not in DEFAULT_MODELS:
            return jsonify(success=False,error='AI answers are not configured. You can read the source-based FAQ answer instead.',error_code='ai_not_configured',can_use_faq=True),503
        if mode=='ai' and not app.config['API_KEY']:
            key_name = 'GEMINI_API_KEY' if app.config['AI_PROVIDER']=='gemini' else 'CCIT_API_KEY'
            app.logger.warning('AI key is missing for provider=%s. Configure %s in the private backend environment and restart Flask.',app.config['AI_PROVIDER'],key_name)
            return jsonify(success=False,error='AI answers are not configured yet. You can read the source-based FAQ answer instead.',error_code='ai_not_configured',can_use_faq=True),503
        try:
            reply=format_faq(records, resolved) if mode=='faq' else generate(resolved,records,app.config['API_KEY'],app.config['MODEL'],app.config['AI_PROVIDER'])
        except Exception as error:
            problem = diagnose(error, app.config['AI_PROVIDER'])
            # Remote error bodies/URLs can contain credentials. Log only fixed
            # classifications, numeric status and our own maintainer guidance.
            app.logger.warning('AI request failed: provider=%s category=%s upstream_status=%s exception=%s. %s',
                app.config['AI_PROVIDER'], problem.code, problem.upstream_status, type(error).__name__, problem.action)
            return jsonify(success=False,error=problem.message,error_code=problem.code,can_use_faq=True),502
        sources, details, warnings = source_metadata(records, app.config['KNOWLEDGE'])
        return jsonify(success=True,reply=reply,mode=mode,sources=sources,details=details,warnings=warnings,context=next_context)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(success=False,error=error.description),error.code
    return app

app=create_app()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=False)
