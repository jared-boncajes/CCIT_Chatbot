"""Offline finder tests: no live credentials or provider requests."""
from types import SimpleNamespace

import httpx2 as httpx
import pytest
from google.genai.errors import APIError

import check_ai
from app import create_app

MODELS = [
    'gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite', 'gemini-2.5-flash-lite',
    'gemini-3.1-flash-lite-image', 'gemini-3.8-flash-preview',
    'gemini-2.5-pro', 'deep-research-preview-fixture',
]
RECORD = {'id': 'TEST-FINDER', 'question': 'What programs does CCIT offer?',
          'answer': 'Synthetic fixture answer', 'keywords': ['programs'],
          'category': 'academic_programs', 'verification_status': 'verified'}
ARGS = SimpleNamespace(list_models=False, test=False, find_model=True)


@pytest.fixture
def application(monkeypatch):
    monkeypatch.setattr(check_ai, 'list_models', lambda *args: MODELS)
    return create_app({'TESTING': True, 'AI_PROVIDER': 'gemini', 'API_KEY': 'synthetic-test-key',
                       'MODEL': 'gemini-2.5-flash-lite', 'KNOWLEDGE': [RECORD]})


def test_candidates_are_stable_text_flash_models_and_skip_current_first():
    assert check_ai.model_candidates(MODELS + MODELS, 'gemini-2.5-flash-lite') == [
        'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-3.8-flash',
    ]


def test_finder_continues_after_404_503_and_keeps_env_private_unchanged(monkeypatch, application, capsys, tmp_path):
    env = tmp_path / '.env'
    before = 'GEMINI_API_KEY=synthetic-test-key\nCCIT_MODEL=gemini-2.5-flash-lite\n'
    env.write_text(before)
    monkeypatch.setattr(check_ai, 'ROOT', tmp_path)
    calls = []

    def generate(question, records, key, model, provider):
        calls.append(model)
        assert records == [RECORD]
        assert question == 'What programs does CCIT offer?'
        assert key == 'synthetic-test-key' and provider == 'gemini'
        if len(calls) < 3:
            status = 404 if len(calls) == 1 else 503
            raise APIError(status, {'error': {'code': status, 'message': 'private synthetic-test-key'}})
        return 'Synthetic successful answer'

    monkeypatch.setattr(check_ai, 'generate', generate)
    assert check_ai.run(ARGS, application) == 0
    output = capsys.readouterr().out
    assert len(calls) == 3
    assert 'ai_model_unavailable' in output and 'ai_provider_unavailable' in output
    assert 'CCIT_MODEL=gemini-3.8-flash' in output
    assert 'synthetic-test-key' not in output
    assert env.read_text() == before
    assert application.config['MODEL'] == 'gemini-2.5-flash-lite'


def test_finder_stops_after_first_success(monkeypatch, application, capsys):
    calls = []

    def generate(*args):
        calls.append(args)
        return 'Synthetic successful answer'

    monkeypatch.setattr(check_ai, 'generate', generate)
    assert check_ai.run(ARGS, application) == 0
    assert len(calls) == 1
    assert 'CCIT_MODEL=gemini-3.5-flash-lite' in capsys.readouterr().out


@pytest.mark.parametrize('error,expected', [
    (APIError(429, {'error': {'code': 429}}), 'ai_quota_exceeded'),
    (APIError(403, {'error': {'code': 403}}), 'ai_access_denied'),
    (APIError(400, {'error': {'code': 400, 'details': [{'reason': 'API_KEY_INVALID'}]}}), 'ai_access_denied'),
    (APIError(400, {'error': {'code': 400}}), 'ai_request_rejected'),
    (httpx.ReadTimeout('private synthetic-test-key'), 'ai_timeout'),
    (httpx.ConnectError('private synthetic-test-key'), 'ai_connection_failed'),
    (TypeError('private synthetic-test-key'), 'ai_sdk_configuration'),
])
def test_finder_stops_on_non_model_errors(monkeypatch, application, capsys, error, expected):
    calls = []

    def fail(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(check_ai, 'generate', fail)
    assert check_ai.run(ARGS, application) == 1
    output = capsys.readouterr().out
    assert expected in output
    assert 'CCIT_MODEL=' not in output
    assert 'synthetic-test-key' not in output
    assert len(calls) == 1


def test_finder_never_exceeds_three_generation_requests(monkeypatch, application, capsys):
    calls = []

    def fail(*args):
        calls.append(args)
        raise APIError(404, {'error': {'code': 404}})

    monkeypatch.setattr(check_ai, 'generate', fail)
    assert check_ai.run(ARGS, application) == 1
    assert len(calls) == 3
    assert 'None of the tested models returned a usable answer' in capsys.readouterr().out


def test_finder_does_not_probe_media_or_preview_models(monkeypatch, application, capsys):
    monkeypatch.setattr(check_ai, 'list_models', lambda *args: ['gemini-3.1-flash-lite-image', 'gemini-3.8-flash-preview'])

    def unexpected(*args):
        raise AssertionError('No generation request should be made')

    monkeypatch.setattr(check_ai, 'generate', unexpected)
    assert check_ai.run(ARGS, application) == 1
    assert 'no generation requests were made' in capsys.readouterr().out


def test_finder_needs_reviewed_source_before_any_remote_request(monkeypatch, application, capsys):
    application.config['KNOWLEDGE'] = []

    def unexpected(*args):
        raise AssertionError('No provider request should be made')

    monkeypatch.setattr(check_ai, 'list_models', unexpected)
    assert check_ai.run(ARGS, application) == 1
    assert 'No reviewed knowledge' in capsys.readouterr().out


def test_finder_refuses_automatic_openai_model_selection(monkeypatch, application, capsys):
    application.config['AI_PROVIDER'] = 'openai'

    def unexpected(*args):
        raise AssertionError('No provider request should be made')

    monkeypatch.setattr(check_ai, 'list_models', unexpected)
    assert check_ai.run(ARGS, application) == 1
    assert 'supports Gemini' in capsys.readouterr().out
