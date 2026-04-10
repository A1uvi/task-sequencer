import logging
from typing import Any

import anthropic
from anthropic import AsyncAnthropic

from ai_providers.base import ProviderMessage, ProviderResponse, QuotaExhaustedError, ProviderError

logger = logging.getLogger(__name__)


def _is_quota_exhausted(exc: anthropic.APIError) -> bool:
    """
    Determine whether an Anthropic API error represents quota exhaustion.

    Handles:
    - anthropic.RateLimitError (HTTP 429)
    - anthropic.APIStatusError with status 429
    - Error type "overloaded_error"
    - Error messages containing "resource_exhausted"
    """
    if isinstance(exc, anthropic.RateLimitError):
        return True

    if isinstance(exc, anthropic.APIStatusError):
        if exc.status_code == 429:
            return True
        # Check error type in response body
        body = exc.body
        if isinstance(body, dict):
            error_type = body.get("error", {}).get("type", "") if isinstance(body.get("error"), dict) else ""
            if error_type == "overloaded_error":
                return True

    # Check error message for resource_exhausted
    if "resource_exhausted" in str(exc).lower():
        return True

    return False


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
    Execute a messages request using the Anthropic Claude API.

    System prompt is passed via the system= parameter (not as a message).
    Messages with role "system" are excluded from the messages list.

    Maps RateLimitError, 429 status, overloaded_error, resource_exhausted
    to QuotaExhaustedError. Maps all other APIError to ProviderError.
    """
    client = AsyncAnthropic(api_key=api_key)

    # Convert ProviderMessage list, excluding system-role messages
    # (system content is passed via the system= parameter instead)
    anthropic_messages: list[dict] = []
    for msg in messages:
        if msg.role == "system":
            continue
        if msg.attachments:
            import base64
            content_parts: list[dict] = []
            text_prefix = ""
            image_parts: list[dict] = []
            for att in msg.attachments:
                if att.content_type.startswith("text/"):
                    try:
                        decoded = base64.b64decode(att.data).decode("utf-8", errors="replace")
                    except Exception:
                        decoded = att.data
                    text_prefix += f"\n[Attachment: {att.filename}]\n{decoded}\n"
                else:
                    image_parts.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": att.content_type,
                            "data": att.data,
                        },
                    })
            content_parts.append({"type": "text", "text": text_prefix + msg.content})
            content_parts.extend(image_parts)
            anthropic_messages.append({"role": msg.role, "content": content_parts})
        else:
            anthropic_messages.append({"role": msg.role, "content": msg.content})

    # Build create() kwargs — only pass system if it's provided
    create_kwargs: dict[str, Any] = {
        "model": model,
        "messages": anthropic_messages,
        "max_tokens": max_tokens,
        **kwargs,
    }
    if system_prompt is not None:
        create_kwargs["system"] = system_prompt

    # Anthropic's API does not accept temperature=0.7 by default without explicit support;
    # it is a valid parameter — include it.
    create_kwargs["temperature"] = temperature

    try:
        response = await client.messages.create(**create_kwargs)
    except anthropic.APIError as exc:
        if _is_quota_exhausted(exc):
            logger.warning("Anthropic quota exhausted: %s", exc)
            raise QuotaExhaustedError(str(exc)) from exc
        logger.warning("Anthropic API error: %s", exc)
        raise ProviderError(str(exc)) from exc

    content = response.content[0].text if response.content else ""
    usage = response.usage

    return ProviderResponse(
        content=content,
        prompt_tokens=usage.input_tokens if usage else 0,
        completion_tokens=usage.output_tokens if usage else 0,
        total_tokens=(usage.input_tokens + usage.output_tokens) if usage else 0,
        raw_response=response.model_dump(),
    )
