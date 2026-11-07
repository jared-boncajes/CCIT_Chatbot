"""SDK transport tests use synthetic records and make no network requests."""
import json

import httpx2 as httpx
import pytest
from google import genai
from openai import OpenAI

from app import create_app
from chatbot import ai_service

RECORD = {
    'id': 'TEST-1', 'question': 'What programs exist?',
    'answer': 'Synthetic source answer', 'keywords': ['programs'],
    'verification_status': 'verified', 'source': 'Synthetic test fixture',
}


def gemini_transport(monkeypatch, status, body):
    requests = []
    original_client = genai.Client

    def handle(request):
        requests.append(request)
        return httpx.Response(status, json=body)

    def client(**kwargs):
        # Isolate the SDK in an in-memory test transport, never a real proxy/API.
        transport = httpx.Client(transport=httpx.MockTransport(handle), trust_env=False)
        kwargs['http_options'] = kwargs['http_options'].model_copy(update={'httpx_client': transport})
        return original_client(**kwargs)

    monkeypatch.setattr(ai_service.genai, 'Client', client)
    return requests


def test_gemini_sdk_serializes_grounding_and_parses_response(monkeypatch):
    requests = gemini_transport(monkeypatch, 200, {
        'candidates': [{'content': {'role': 'model', 'parts': [{'text': 'Synthetic generated answer'}]}, 'finishReason': 'STOP'}],
    })
    result = ai_service.generate('What programs exist?', [RECORD], 'synthetic-test-key', 'gemini-test-model', 'gemini')
    assert result == 'Synthetic generated answer'
    assert len(requests) == 1
    assert requests[0].url.host == 'generativelanguage.googleapis.com'
    assert requests[0].url.path.endswith('/models/gemini-test-model:generateContent')
    body = json.loads(requests[0].content)
    assert body['systemInstruction']['parts'][0]['text'] == ai_service.SYSTEM
    content = json.loads(body['contents'][0]['parts'][0]['text'])
    assert content == {'question': 'What programs exist?', 'sources': [RECORD]}
    assert body['generationConfig']['maxOutputTokens'] == 2048
    assert requests[0].extensions['timeout']['read'] == 25


@pytest.mark.parametrize('parts', [[], [{'text': '  '}]] )
def test_gemini_empty_or_blocked_response_is_an_error(monkeypatch, parts):
    gemini_transport(monkeypatch, 200, {
        'candidates': [{'content': {'role': 'model', 'parts': parts}, 'finishReason': 'SAFETY'}],
    })
    with pytest.raises(ValueError, match='Empty provider response'):
        ai_service.generate('programs', [RECORD], 'synthetic-test-key', 'gemini-test-model', 'gemini')


def test_gemini_quota_error_is_not_retried_or_exposed(monkeypatch):
    requests = gemini_transport(monkeypatch, 429, {
        'error': {'code': 429, 'status': 'RESOURCE_EXHAUSTED', 'message': 'sensitive synthetic detail'},
    })
    client = create_app({'TESTING': True, 'CHAT_MODE': 'ai', 'AI_PROVIDER': 'gemini',
                         'API_KEY': 'synthetic-test-key', 'MODEL': 'gemini-test-model', 'KNOWLEDGE': [RECORD]}).test_client()
    response = client.post('/api/chat', json={'message': 'programs'})
    assert response.status_code == 502
    assert response.get_json()['success'] is False
    assert b'sensitive synthetic detail' not in response.data
    assert b'synthetic-test-key' not in response.data
    assert len(requests) == 1


def test_openai_still_uses_responses_api(monkeypatch):
    original_client = OpenAI
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={
            'id': 'resp_synthetic', 'object': 'response', 'created_at': 0,
            'status': 'completed', 'model': 'openai-test-model',
            'output': [{'id': 'msg_synthetic', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                        'content': [{'type': 'output_text', 'text': 'Synthetic OpenAI answer', 'annotations': []}]}],
        })

    def client(**kwargs):
        return original_client(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handle), trust_env=False))

    monkeypatch.setattr(ai_service, 'OpenAI', client)
    assert ai_service.generate('programs', [RECORD], 'synthetic-test-key', 'openai-test-model', 'openai') == 'Synthetic OpenAI answer'
    assert len(requests) == 1
    assert requests[0].url.host == 'api.openai.com'
    assert requests[0].url.path == '/v1/responses'
    assert json.loads(requests[0].content)['instructions'] == ai_service.SYSTEM


@pytest.mark.parametrize('provider,key_name,expected_key', [
    ('gemini', 'GEMINI_API_KEY', 'synthetic-test-key'),
    ('gemini', 'GOOGLE_API_KEY', 'synthetic-test-key'),
    ('openai', 'CCIT_API_KEY', 'synthetic-test-key'),
    ('openai', 'OPENAI_API_KEY', 'synthetic-test-key'),
    ('gemini', 'CCIT_API_KEY', None),
    ('openai', 'GEMINI_API_KEY', None),
])
def test_provider_key_selection(monkeypatch, caplog, provider, key_name, expected_key):
    for name in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'CCIT_API_KEY', 'OPENAI_API_KEY', 'CCIT_MODEL']:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('CCIT_AI_PROVIDER', provider)
    monkeypatch.setenv('CHAT_MODE', 'ai')
    monkeypatch.setenv(key_name, 'synthetic-test-key')
    application = create_app({'TESTING': True, 'KNOWLEDGE': [RECORD]})
    assert application.config['API_KEY'] == expected_key
    assert application.config['MODEL'] == ai_service.DEFAULT_MODELS[provider]
    client = application.test_client()
    health = client.get('/api/health').get_json()
    assert health['provider'] == provider
    assert health['ready'] is bool(expected_key)
    assert 'synthetic-test-key' not in json.dumps(health)
    if expected_key is None:
        response = client.post('/api/chat', json={'message': 'programs'})
        assert response.status_code == 503
        required = 'GEMINI_API_KEY' if provider == 'gemini' else 'CCIT_API_KEY'
        assert required in caplog.text
        assert response.get_json()['error_code'] == 'ai_not_configured'
        assert response.get_json()['can_use_faq'] is True


def test_invalid_provider_is_reported_without_calling_sdk(monkeypatch):
    monkeypatch.setenv('CCIT_AI_PROVIDER', 'invalid-provider')
    application = create_app({'TESTING': True, 'CHAT_MODE': 'ai', 'API_KEY': 'synthetic-test-key', 'KNOWLEDGE': [RECORD]})
    client = application.test_client()
    assert not client.get('/api/health').get_json()['ready']
    assert client.post('/api/chat', json={'message': 'programs'}).status_code == 503


@pytest.mark.parametrize('status,detail,expected', [
    (400, {'reason': 'API_KEY_INVALID'}, 'ai_access_denied'),
    (400, {}, 'ai_request_rejected'),
    (403, {}, 'ai_access_denied'),
    (404, {}, 'ai_model_unavailable'),
    (429, {}, 'ai_quota_exceeded'),
    (503, {}, 'ai_provider_unavailable'),
])
def test_provider_errors_have_specific_safe_messages(monkeypatch, caplog, status, detail, expected):
    requests = gemini_transport(monkeypatch, status, {
        'error': {'code': status, 'message': 'sensitive detail containing synthetic-test-key', 'details': [detail]},
    })
    client = create_app({'TESTING': True, 'CHAT_MODE': 'ai', 'AI_PROVIDER': 'gemini',
                         'API_KEY': 'synthetic-test-key', 'MODEL': 'gemini-test-model', 'KNOWLEDGE': [RECORD]}).test_client()
    response = client.post('/api/chat', json={'message': 'programs'})
    assert response.status_code == 502
    assert response.get_json()['error_code'] == expected
    assert expected in caplog.text
    assert f'upstream_status={status}' in caplog.text
    for secret in ['synthetic-test-key', 'sensitive detail']:
        assert secret not in response.get_data(as_text=True)
        assert secret not in caplog.text
    assert len(requests) == 1


def test_model_listing_filters_compatible_models_without_generation(monkeypatch):
    requests = gemini_transport(monkeypatch, 200, {'models': [
        {'name': 'models/gemini-text-fixture', 'supportedGenerationMethods': ['generateContent', 'countTokens']},
        {'name': 'models/embedding-fixture', 'supportedGenerationMethods': ['embedContent']},
        {'name': 'models/metadata-only-fixture'},
    ]})
    assert ai_service.list_models('synthetic-test-key', 'gemini') == ['gemini-text-fixture']
    assert len(requests) == 1
    assert requests[0].method == 'GET'
    assert requests[0].url.path.endswith('/models')


@pytest.mark.parametrize('error_type,expected', [
    (httpx.ReadTimeout, 'ai_timeout'),
    (httpx.ConnectError, 'ai_connection_failed'),
])
def test_network_failures_are_classified_without_raw_errors(monkeypatch, caplog, error_type, expected):
    original_client = genai.Client

    def handle(request):
        raise error_type('sensitive detail containing synthetic-test-key', request=request)

    def client_factory(**kwargs):
        transport = httpx.Client(transport=httpx.MockTransport(handle), trust_env=False)
        kwargs['http_options'] = kwargs['http_options'].model_copy(update={'httpx_client': transport})
        return original_client(**kwargs)

    monkeypatch.setattr(ai_service.genai, 'Client', client_factory)
    client = create_app({'TESTING': True, 'CHAT_MODE': 'ai', 'AI_PROVIDER': 'gemini',
                         'API_KEY': 'synthetic-test-key', 'MODEL': 'gemini-test-model', 'KNOWLEDGE': [RECORD]}).test_client()
    response = client.post('/api/chat', json={'message': 'programs'})
    assert response.status_code == 502
    assert response.get_json()['error_code'] == expected
    assert 'synthetic-test-key' not in response.get_data(as_text=True) + caplog.text
