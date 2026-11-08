"""Map provider failures to fixed messages without echoing remote error text."""
import httpx2 as httpx
from google.genai import errors as google_errors
from openai import APIConnectionError, APIStatusError, APITimeoutError


class EmptyResponseError(ValueError):
    """The provider returned no usable answer."""


class AIProblem:
    """A small container for a safe error code, message and troubleshooting step."""

    def __init__(self, code, message, action, upstream_status=None):
        self.code = code
        self.message = message
        self.action = action
        self.upstream_status = upstream_status


def diagnose(error, provider):
    """Inspect structured codes only; never return or log the exception itself."""
    label = 'Gemini' if provider == 'gemini' else 'OpenAI'
    key_name = 'GEMINI_API_KEY' if provider == 'gemini' else 'CCIT_API_KEY'
    status = None
    reasons = set()
    if isinstance(error, google_errors.APIError):
        status = error.code if isinstance(error.code, int) else None
        payload = error.details if isinstance(error.details, dict) else {}
        payload = payload.get('error', payload)
        if isinstance(payload, dict):
            details = payload.get('details', [])
            for detail in details if isinstance(details, list) else []:
                if isinstance(detail, dict) and isinstance(detail.get('reason'), str):
                    reasons.add(detail['reason'])
    elif isinstance(error, APIStatusError):
        status = error.status_code
        if isinstance(error.code, str):
            reasons.add(error.code)

    if status in (401, 403) or reasons & {'API_KEY_INVALID', 'API_KEY_EXPIRED', 'invalid_api_key'}:
        return AIProblem(
            'ai_access_denied', f'{label} rejected the API key or project access. The chatbot maintainer needs to check the AI credentials.',
            f'Check {key_name} in the private .env and the key/project API restrictions. Save and restart Flask.', status,
        )
    if status == 404 or 'model_not_found' in reasons:
        return AIProblem(
            'ai_model_unavailable', f'The selected {label} model is unavailable for this project. The chatbot maintainer needs to update the model setting.',
            'Run check_ai.py --list-models, set CCIT_MODEL to an available text model ID, then restart Flask.', status,
        )
    if status == 429:
        return AIProblem(
            'ai_quota_exceeded', f'{label} reports a quota or rate limit for this project or model. Please check the available allowance before retrying.',
            'Check model/project quota in the provider console. Model listing does not guarantee free quota; wait for a rate-limit reset when applicable.', status,
        )
    if isinstance(error, (APITimeoutError, httpx.TimeoutException, TimeoutError)) or status in (408, 504):
        return AIProblem(
            'ai_timeout', f'{label} took too long to respond. Please try again.',
            'Check the internet connection and provider availability, then retry.', status,
        )
    if isinstance(error, (APIConnectionError, httpx.TransportError, ConnectionError)):
        return AIProblem(
            'ai_connection_failed', f'The chatbot could not connect to {label}. Please check the server connection and try again.',
            'Check internet/proxy/firewall access and TLS trust for the provider endpoint. Keep TLS verification enabled.', status,
        )
    if isinstance(error, EmptyResponseError):
        return AIProblem(
            'ai_empty_response', f'{label} returned no usable answer. Please try rephrasing your question.',
            'Check the selected model capabilities and response limits. A blocked or empty result is not a successful answer.', status,
        )
    if isinstance(error, TypeError):
        return AIProblem(
            'ai_sdk_configuration', 'The AI client could not be configured. The chatbot maintainer needs to update the server dependencies.',
            'Install requirements.txt using the same Python environment that runs app.py, then restart Flask.', status,
        )
    if status in (400, 422):
        return AIProblem(
            'ai_request_rejected', f'{label} rejected the request configuration. The chatbot maintainer needs to check the selected model and project settings.',
            'Run check_ai.py --list-models and check_ai.py --test. Check model support, API key and project restrictions in the provider console.', status,
        )
    if status is not None and status >= 500:
        return AIProblem(
            'ai_provider_unavailable', f'{label} is temporarily unavailable. Please try again shortly.',
            'Check provider service status and retry later.', status,
        )
    return AIProblem(
        'ai_unavailable', 'The AI service is unavailable. Please try again shortly.',
        'Run check_ai.py --test and verify the installed dependencies and provider configuration.', status,
    )
