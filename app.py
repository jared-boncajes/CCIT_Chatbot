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
from chatbot.intent_model import load_model
from chatbot.scope import scope_candidates
from chatbot.roster import focus_roster, is_roster_request
from research.web import analysis_blueprint

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
        'categories': {'academic_programs', 'bsit', 'bscs', 'bsemc', 'accreditation', 'careers', 'curriculum', 'prerequisites', 'ojt'},
        'note': 'Explore programs, curricula, course prerequisites, careers, and OJT requirements from the supplied knowledge base.',
    },
    {
        'id': 'services',
        'title': 'Student Services',
        'description': 'Find information on enrollment, forms, and department procedures.',
        'categories': {'scholarships', 'dost', 'activities', 'organizations', 'community-service'},
        'note': 'Explore scholarships, student organizations, events, and community service from the supplied knowledge base.',
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
    """Create the Flask app, load its files, and connect URLs to functions."""
    app = Flask(__name__)

    # Read private settings once when Flask starts. Never send the key to JavaScript.
    provider = os.getenv('CCIT_AI_PROVIDER', 'openai').strip().lower()
    if provider == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    elif provider == 'openai':
        api_key = os.getenv('CCIT_API_KEY') or os.getenv('OPENAI_API_KEY')
    else:
        api_key = None

    knowledge_path = ROOT / 'data/knowledge.json'
    knowledge_text = knowledge_path.read_text(encoding='utf-8')
    knowledge = json.loads(knowledge_text)

    app.config.update(
        MAX_CONTENT_LENGTH=16384,
        CHAT_MODE=os.getenv('CHAT_MODE', 'ai'),
        AI_PROVIDER=provider,
        API_KEY=api_key,
        MODEL=os.getenv('CCIT_MODEL') or DEFAULT_MODELS.get(provider, ''),
        KNOWLEDGE=knowledge,
    )
    # Tests can supply small settings without changing the real .env or data file.
    if test_config:
        app.config.update(test_config)
    app.config.setdefault('ANALYSIS_ROOT', ROOT / 'research/results')
    model_path = Path(app.config['ANALYSIS_ROOT']) / 'model.json'
    app.config['INTENT_MODEL'] = load_model(model_path, app.config['KNOWLEDGE'])

    # The course-analysis page has its own routes in research/web.py.
    app.register_blueprint(analysis_blueprint)

    @app.get('/')
    def index():
        return render_template('index.html', topics=TOPICS)

    @app.get('/api/health')
    def health():
        records = app.config['KNOWLEDGE']
        reviewed_count = 0
        for record in records:
            if record.get('verification_status') == 'verified':
                reviewed_count += 1

        supported_provider = app.config['AI_PROVIDER'] in DEFAULT_MODELS
        ai_configured = supported_provider and bool(app.config['API_KEY'])
        mode = app.config['CHAT_MODE']
        ready = False
        if reviewed_count > 0:
            if mode == 'faq':
                ready = True
            elif mode == 'ai' and ai_configured:
                ready = True

        return jsonify(
            success=True,
            ready=ready,
            mode=mode,
            knowledge_records=len(records),
            verified_records=reviewed_count,
            ai_configured=ai_configured,
            provider=app.config['AI_PROVIDER'],
            intent_model_ready=app.config['INTENT_MODEL'] is not None,
        )

    @app.get('/api/suggestions')
    def suggestions():
        reviewed = []
        for record in app.config['KNOWLEDGE']:
            if record.get('verification_status') == 'verified':
                reviewed.append(record)

        topics = []
        for topic in TOPICS:
            questions = []
            for record in reviewed:
                if record.get('category') in topic['categories']:
                    questions.append(record['question'])
            topics.append({
                'id': topic['id'],
                'title': topic['title'],
                'note': topic['note'],
                'questions': questions,
            })

        first_questions = []
        for record in reviewed[:6]:
            first_questions.append(record['question'])
        return jsonify(success=True, questions=first_questions, topics=topics)

    @app.post('/api/chat')
    def chat():
        """Follow a question from input checking to its final JSON answer."""
        # 1. Read and check the question sent by static/js/script.js.
        body = request.get_json(silent=True)
        message = None
        if isinstance(body, dict):
            message = body.get('message')
        if not isinstance(message, str) or not message.strip() or len(message) > 1000:
            return jsonify(
                success=False,
                error='Enter a question between 1 and 1,000 characters.',
            ), 400
        message = message.strip()

        # 2. Only accept the small context format and explicit FAQ fallback.
        if body.get('mode') not in (None, 'faq'):
            return jsonify(success=False, error='The requested answer mode is not supported.'), 400
        try:
            context = read_context(body.get('context'))
        except ValueError:
            return jsonify(
                success=False,
                error='The conversation context is not valid. Please start a new chat.',
            ), 400

        # 3. Privacy requests and greetings do not need retrieval or an AI call.
        if is_private_question(message):
            return jsonify(
                success=True,
                reply='I cannot access private student records. Please use the official student services channels.',
                sources=[], mode='privacy', context=context,
            )
        greeting_pattern = r'(?:hi|hello|hey|kumusta|magandang araw|thanks|thank you|salamat)[ !.]*'
        if re.fullmatch(greeting_pattern, message, re.I):
            return jsonify(
                success=True,
                reply='Hello! Ask me about CCIT programs, scholarships, faculty, or facilities.',
                sources=[], mode='greeting', context=context,
            )

        # 4. Make sure the knowledge file and requested mode are available.
        if not app.config['KNOWLEDGE']:
            return jsonify(
                success=False,
                error='The About CCIT knowledge document has not been imported yet. Department answers are unavailable.',
            ), 503
        mode = body.get('mode') or app.config['CHAT_MODE']
        if mode not in ('ai', 'faq'):
            return jsonify(success=False, error='The chatbot mode is not configured correctly.'), 503

        # 5. Resolve a follow-up such as "What jobs after this program?".
        resolved, next_context, needs_program = resolve_question(message, context)
        if needs_program:
            return jsonify(
                success=True,
                reply='Which program do you mean: BSCS, BSIT, or BSEMC?',
                sources=[], mode='clarification', context=next_context,
            )

        # 6. Select reviewed, source-supported records. No source means no answer.
        _, clarification, pending = scope_candidates(resolved, app.config['KNOWLEDGE'])
        if clarification:
            return jsonify(success=True, reply=clarification, sources=[], mode='clarification',
                           context={**next_context, **pending})
        records = retrieve(resolved, app.config['KNOWLEDGE'], app.config['INTENT_MODEL'])
        if not records:
            return jsonify(success=True, reply=FALLBACK, sources=[], mode='fallback', context=next_context)

        # 7. AI mode needs a supported provider and a private key. FAQ mode does not.
        if mode == 'ai':
            if app.config['AI_PROVIDER'] not in DEFAULT_MODELS:
                return jsonify(
                    success=False,
                    error='AI answers are not configured. You can read the source-based FAQ answer instead.',
                    error_code='ai_not_configured', can_use_faq=True,
                ), 503
            if not app.config['API_KEY']:
                if app.config['AI_PROVIDER'] == 'gemini':
                    key_name = 'GEMINI_API_KEY'
                else:
                    key_name = 'CCIT_API_KEY'
                app.logger.warning(
                    'AI key is missing for provider=%s. Configure %s in the private backend environment and restart Flask.',
                    app.config['AI_PROVIDER'], key_name,
                )
                return jsonify(
                    success=False,
                    error='AI answers are not configured yet. You can read the source-based FAQ answer instead.',
                    error_code='ai_not_configured', can_use_faq=True,
                ), 503

        # 8. Build a local FAQ answer or ask the configured AI to phrase the sources.
        answer_records = focus_roster(records, resolved)
        if is_roster_request(resolved):
            next_context['topic'] = 'representatives'
        try:
            if mode == 'faq':
                reply = format_faq(answer_records, resolved)
            else:
                reply = generate(
                    resolved, answer_records, app.config['API_KEY'],
                    app.config['MODEL'], app.config['AI_PROVIDER'],
                )
        except Exception as error:
            problem = diagnose(error, app.config['AI_PROVIDER'])
            # Provider errors can contain secrets. Log our fixed diagnosis only.
            app.logger.warning(
                'AI request failed: provider=%s category=%s upstream_status=%s exception=%s. %s',
                app.config['AI_PROVIDER'], problem.code, problem.upstream_status,
                type(error).__name__, problem.action,
            )
            return jsonify(
                success=False, error=problem.message,
                error_code=problem.code, can_use_faq=True,
            ), 502

        # 9. Return JSON. The frontend displays the answer, not the source metadata.
        sources, details, warnings = source_metadata(records, app.config['KNOWLEDGE'])
        return jsonify(
            success=True, reply=reply, mode=mode, sources=sources,
            details=details, warnings=warnings, context=next_context,
        )

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(success=False, error=error.description), error.code
    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
