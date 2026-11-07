"""Check AI setup without printing credentials or raw provider errors."""
import argparse
from importlib.metadata import version

from app import ROOT, create_app
from chatbot.ai_service import DEFAULT_MODELS, generate, list_models
from chatbot.errors import diagnose
from chatbot.retriever import retrieve


def run(args, application):
    config = application.config
    provider = config['AI_PROVIDER']
    print('Local .env beside app.py:', 'found' if (ROOT / '.env').is_file() else 'not found')
    print('Provider:', provider if provider in DEFAULT_MODELS else 'unsupported')
    print('Chat mode:', config['CHAT_MODE'])
    # Guard against accidentally pasting a credential into the model field.
    model = config['MODEL']
    safe_model = model if not model.startswith(('AIza', 'sk-')) else '[hidden: looks like a key; use a model ID instead]'
    print('Configured model:', safe_model)
    print('API key:', 'present (hidden)' if config['API_KEY'] else 'missing')
    if provider not in DEFAULT_MODELS:
        print('Set CCIT_AI_PROVIDER to gemini or openai in .env, then restart Flask.')
        return 1
    package = 'google-genai' if provider == 'gemini' else 'openai'
    print('SDK:', package, version(package))
    if not config['API_KEY']:
        name = 'GEMINI_API_KEY' if provider == 'gemini' else 'CCIT_API_KEY'
        print(f'Add {name} privately to .env beside app.py. Do not paste the key into chat or GitHub.')
        return 1
    if not (args.list_models or args.test):
        print('Configuration only; the key has not been validated.')
        print('Use --list-models to list model IDs, or --test for one grounded generation request.')
        return 0
    try:
        if args.list_models:
            models = list_models(config['API_KEY'], provider)
            if not models:
                print('No compatible model IDs were returned. Check this key/project in the provider console.')
                return 1
            print('Model IDs returned by the provider:')
            for name in models:
                print(' -', name)
            print('Set CCIT_MODEL to a suitable text model ID from this list, save .env, and restart Flask.')
            print('Listing a model does not guarantee free-tier quota or generation access.')
            return 0
        question = 'What programs does CCIT offer?'
        records = retrieve(question, config['KNOWLEDGE'])
        if not records:
            print('No reviewed knowledge was retrieved for the test; no provider request was made.')
            return 1
        generate(question, records, config['API_KEY'], model, provider)
        print('Live generation succeeded using the configured model and retrieved source context.')
        print('Response content is omitted. Review its factual accuracy through the chatbot.')
        return 0
    except Exception as error:
        problem = diagnose(error, provider)
        print('Diagnostic code:', problem.code)
        if problem.upstream_status is not None:
            print('Upstream HTTP status:', problem.upstream_status)
        print(problem.message)
        print('Next step:', problem.action)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--list-models', action='store_true', help='List model IDs without generating an answer')
    action.add_argument('--test', action='store_true', help='Make one real, grounded generation request')
    return run(parser.parse_args(), create_app())


if __name__ == '__main__':
    raise SystemExit(main())
