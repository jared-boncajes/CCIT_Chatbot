"""Check AI setup without printing credentials or raw provider errors."""
import argparse
import re
from importlib.metadata import version

from app import ROOT, create_app
from chatbot.ai_service import DEFAULT_MODELS, generate, list_models
from chatbot.errors import diagnose
from chatbot.retriever import retrieve


MAX_MODEL_TESTS = 3


def model_candidates(models, configured):
    """Prefer recent stable Flash-Lite IDs, then Flash; exclude media/probes."""
    ranked = []
    for model in set(models):
        match = re.fullmatch(r'gemini-(\d+)\.(\d+)-(flash-lite|flash)', model)
        if not match:
            continue
        major, minor, kind = match.groups()
        rank = (model == configured.removeprefix('models/'), kind != 'flash-lite', -int(major), -int(minor))
        ranked.append((rank, model))
    return [model for _, model in sorted(ranked)[:MAX_MODEL_TESTS]]


def find_working_model(config, question, records):
    candidates = model_candidates(list_models(config['API_KEY'], 'gemini'), config['MODEL'])
    if not candidates:
        print('No stable Gemini Flash/Flash-Lite text model IDs were returned; no generation requests were made.')
        return 1
    print(f'Testing at most {len(candidates)} models with one grounded request each; this uses API quota.', flush=True)
    print('This does not enable billing or guarantee free quota. The .env file will not be changed.', flush=True)
    for index, model in enumerate(candidates, 1):
        print(f'Testing {index}/{len(candidates)}: {model}', flush=True)
        try:
            generate(question, records, config['API_KEY'], model, 'gemini')
        except Exception as error:
            problem = diagnose(error, 'gemini')
            print('Diagnostic code:', problem.code, flush=True)
            if problem.upstream_status is not None:
                print('Upstream HTTP status:', problem.upstream_status, flush=True)
            # Only model-specific absence/availability/empty results justify
            # trying another ID. Stop on quota, access or connection errors.
            if problem.code in {'ai_model_unavailable', 'ai_provider_unavailable', 'ai_empty_response'}:
                continue
            print('Model search stopped:', problem.message)
            print('Next step:', problem.action)
            return 1
        print('Live generation succeeded for this test. Copy this line into your private .env:')
        print(f'CCIT_MODEL={model}')
        print('Save .env and restart Flask. Keep the same API key. No further models were tested.')
        return 0
    print('None of the tested models returned a usable answer. The .env file was not changed.')
    print('Share the tested model IDs, diagnostic codes and HTTP statuses only; keep your key private.')
    return 1


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
    find_model = getattr(args, 'find_model', False)
    if find_model and provider != 'gemini':
        print('--find-model supports Gemini Flash/Flash-Lite text models only. Use --test for the configured OpenAI model.')
        return 1
    if not (args.list_models or args.test or find_model):
        print('Configuration only; the key has not been validated.')
        print('Use --list-models for model IDs, --test for the configured model, or --find-model to test up to three Gemini text models.')
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
        if find_model:
            return find_working_model(config, question, records)
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
    action.add_argument('--find-model', action='store_true', help='Test up to three listed stable Gemini Flash/Flash-Lite models; stop at first success or quota/access/connection error; never change .env')
    return run(parser.parse_args(), create_app())


if __name__ == '__main__':
    raise SystemExit(main())
