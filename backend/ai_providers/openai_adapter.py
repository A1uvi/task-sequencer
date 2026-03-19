import logging
from typing import Any

import openai
from openai import AsyncOpenAI

from ai_providers.base import ProviderMessage, ProviderResponse, QuotaExhaustedError, ProviderError

logger = logging.getLogger(__name__)

# Error codes that indicate quota exhaustion
_QUOTA_ERROR_CODES = {"insufficient_quota", "billing_limit_exceeded"}


async def execute(
    provider: str,
    model: str,
    messages: list[ProviderMessage],
    api_key: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs: Any
) -> ProviderResponse:
    """
    Execute a chat completion request using the OpenAI API.

    Maps HTTP 429 / RateLimitError / quota error codes to QuotaExhaustedError.
    Maps all other APIError subclasses to ProviderError.
    """
    client = AsyncOpenAI(api_key=api_key)

    # Build messages list, injecting system prompt at index 0 if provided
    openai_messages: list[dict[str, str]] = []
    if system_prompt is not None:
        openai_messages.append({"role": "system", "content": system_prompt})

    for msg in messages:
        openai_messages.append({"role": msg.role, "content": msg.content})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    except openai.RateLimitError as exc:
        logger.warning("OpenAI rate limit / quota exhausted: %s", exc)
        raise QuotaExhaustedError(str(exc)) from exc
    except openai.APIStatusError as exc:
        # Check for quota-related error codes in the response body
        error_code = None
        if exc.body and isinstance(exc.body, dict):
            error_obj = exc.body.get("error", {})
            error_code = error_obj.get("code") if isinstance(error_obj, dict) else None

        if exc.status_code == 429 or error_code in _QUOTA_ERROR_CODES:
            logger.warning("OpenAI quota exhausted (status %s, code %s): %s", exc.status_code, error_code, exc)
            raise QuotaExhaustedError(str(exc)) from exc

        logger.warning("OpenAI API error (status %s): %s", exc.status_code, exc)
        raise ProviderError(str(exc)) from exc
    except openai.APIError as exc:
        logger.warning("OpenAI API error: %s", exc)
        raise ProviderError(str(exc)) from exc

    content = response.choices[0].message.content or ""
    usage = response.usage

    return ProviderResponse(
        content=content,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
        raw_response=response.model_dump(),
    )
