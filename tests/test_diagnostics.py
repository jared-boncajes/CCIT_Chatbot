from types import SimpleNamespace

from google.genai.errors import APIError

import check_ai
from app import create_app
from chatbot.errors import diagnose


def test_cli_reports_safe_model_list(monkeypatch, capsys):
    application = create_app({'AI_PROVIDER': 'gemini', 'API_KEY': 'synthetic-test-key', 'MODEL': 'gemini-test-model'})
    monkeypatch.setattr(check_ai, 'list_models', lambda *args: ['gemini-text-fixture'])
    result = check_ai.run(SimpleNamespace(list_models=True, test=False), application)
    output = capsys.readouterr().out
    assert result == 0 and 'gemini-text-fixture' in output
    assert 'does not guarantee free-tier quota' in output
    assert 'synthetic-test-key' not in output


def test_cli_provider_failure_never_prints_raw_error(monkeypatch, capsys):
    application = create_app({'AI_PROVIDER': 'gemini', 'API_KEY': 'synthetic-test-key', 'MODEL': 'gemini-test-model'})

    def fail(*args):
        raise APIError(403, {'error': {'code': 403, 'message': 'secret synthetic-test-key'}})

    monkeypatch.setattr(check_ai, 'list_models', fail)
    result = check_ai.run(SimpleNamespace(list_models=True, test=False), application)
    output = capsys.readouterr().out
    assert result == 1 and 'ai_access_denied' in output and '403' in output
    assert 'synthetic-test-key' not in output


def test_cli_missing_key_does_not_make_provider_request(monkeypatch, capsys):
    application = create_app({'AI_PROVIDER': 'gemini', 'API_KEY': None, 'MODEL': 'gemini-test-model'})

    def unexpected(*args):
        raise AssertionError('Should not call a provider without a key')

    monkeypatch.setattr(check_ai, 'list_models', unexpected)
    assert check_ai.run(SimpleNamespace(list_models=True, test=False), application) == 1
    assert 'Add GEMINI_API_KEY privately' in capsys.readouterr().out


def test_cli_hides_a_key_pasted_into_model_setting(capsys):
    accidental_key = 'AIza' + 'x' * 35
    application = create_app({'AI_PROVIDER': 'gemini', 'API_KEY': 'synthetic-test-key', 'MODEL': accidental_key})
    assert check_ai.run(SimpleNamespace(list_models=False, test=False), application) == 0
    output = capsys.readouterr().out
    assert accidental_key not in output
    assert 'looks like a key' in output


def test_malformed_provider_details_do_not_break_error_handler():
    problem = diagnose(APIError(400, {'error': {'details': 7, 'message': 'private fixture'}}), 'gemini')
    assert problem.code == 'ai_request_rejected'
    assert 'private fixture' not in problem.message
