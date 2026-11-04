import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from chatbot.retriever import retrieve
from chatbot.ai_service import generate

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')
FALLBACK = "I don't currently have verified information about that. Please contact the CCIT department office for assistance."

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16384, CHAT_MODE=os.getenv('CHAT_MODE','ai'),
        API_KEY=os.getenv('CCIT_API_KEY') or os.getenv('OPENAI_API_KEY'),
        MODEL=os.getenv('CCIT_MODEL','gpt-4.1-mini'),
        KNOWLEDGE=json.loads((ROOT/'data/knowledge.json').read_text()))
    if test_config:
        app.config.update(test_config)

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/health')
    def health():
        records=app.config['KNOWLEDGE']
        count=sum(r.get('verification_status')=='verified' for r in records)
        ready=bool(count and (app.config['CHAT_MODE']=='faq' or app.config['API_KEY']))
        return jsonify(success=True, ready=ready, mode=app.config['CHAT_MODE'],
            knowledge_records=len(records), verified_records=count,
            ai_configured=bool(app.config['API_KEY']))

    @app.get('/api/suggestions')
    def suggestions():
        return jsonify(success=True, questions=[r['question'] for r in app.config['KNOWLEDGE'] if r.get('verification_status')=='verified'][:6])

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
        if app.config['CHAT_MODE']=='ai' and not app.config['API_KEY']:
            return jsonify(success=False,error='AI service is not configured. The maintainer must add an API key, or explicitly enable FAQ retrieval mode.'),503
        records=retrieve(message, app.config['KNOWLEDGE'])
        if not records:
            return jsonify(success=True,reply=FALLBACK,sources=[],mode='fallback')
        try:
            reply='\n\n'.join(r['answer'] for r in records) if app.config['CHAT_MODE']=='faq' else generate(message,records,app.config['API_KEY'],app.config['MODEL'])
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
