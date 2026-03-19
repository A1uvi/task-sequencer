import logging
from typing import Any

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted

from ai_providers.base import ProviderMessage, ProviderResponse, QuotaExhaustedError, ProviderError

logger = logging.getLogger(__name__)


def _convert_messages(
    messages: list[ProviderMessage],
    system_prompt: str | None = None,
) -> list[dict[str, Any]]:
    """
    Convert a list of ProviderMessages to Gemini's history format.

    Gemini roles: "user" and "model" (not "assistant").
    System prompt is prepended to the content of the first user message.
    """
    gemini_messages: list[dict[str, Any]] = []

    system_injected = False
    for msg in messages:
        if msg.role == "system":
            # Skip system-role messages; handled via system_prompt param
            continue

        role = "model" if msg.role == "assistant" else "user"
        content = msg.content

        # Prepend system prompt to the first user message
        if not system_injected and system_prompt is not None and role == "user":
            content = f"{system_prompt}\n\n{content}"
            system_injected = True

        gemini_messages.append({"role": role, "parts": [content]})

    return gemini_messages


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
    Execute a generation request using the Google Gemini API.

    System prompt is prepended to the first user message content.
    Gemini uses "model" for assistant role (not "assistant").

    Maps ResourceExhausted / HTTP 429 to QuotaExhaustedError.
    Maps all other Google API errors to ProviderError.
    """
    genai.configure(api_key=api_key)

    gemini_messages = _convert_messages(messages, system_prompt)

    # Separate the last message as the prompt; the rest form the history
    if not gemini_messages:
        raise ProviderError("No messages provided to Gemini adapter.")

    *history, last_message = gemini_messages

    # Extract the text content from the last message parts
    last_content = last_message["parts"][0] if last_message["parts"] else ""

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    gemini_model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
    )

    try:
        chat = gemini_model.start_chat(history=history)
        response = await chat.send_message_async(last_content, **kwargs)
    except ResourceExhausted as exc:
        logger.warning("Gemini quota exhausted (ResourceExhausted): %s", exc)
        raise QuotaExhaustedError(str(exc)) from exc
    except GoogleAPIError as exc:
        # Check for HTTP 429 in the error message or status
        error_str = str(exc).lower()
        if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
            logger.warning("Gemini quota exhausted (GoogleAPIError): %s", exc)
            raise QuotaExhaustedError(str(exc)) from exc
        logger.warning("Gemini API error: %s", exc)
        raise ProviderError(str(exc)) from exc
    except Exception as exc:
        logger.warning("Gemini unexpected error: %s", exc)
        raise ProviderError(str(exc)) from exc

    content = response.text if hasattr(response, "text") else ""

    # Gemini may not always provide token counts — use 0 as fallback
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is not None:
        prompt_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
        completion_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0
        total_tokens = getattr(usage_metadata, "total_token_count", 0) or (prompt_tokens + completion_tokens)

    # Build raw_response from available attributes
    raw_response: dict[str, Any] = {}
    try:
        # Attempt to get a dict-like representation
        if hasattr(response, "_pb"):
            from google.protobuf.json_format import MessageToDict
            raw_response = MessageToDict(response._pb)
        else:
            raw_response = {"text": content}
    except Exception:
        raw_response = {"text": content}

    return ProviderResponse(
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        raw_response=raw_response,
    )
