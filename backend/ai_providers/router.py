from typing import Any

from ai_providers.base import ProviderMessage, ProviderResponse, ProviderError
import ai_providers.openai_adapter as openai_adapter
import ai_providers.claude_adapter as claude_adapter
import ai_providers.gemini_adapter as gemini_adapter


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
    Route an AI execution request to the correct adapter based on the provider string.

    Supported providers: "openai", "claude", "gemini".
    Raises ProviderError for unknown provider strings.
    """
    if provider == "openai":
        return await openai_adapter.execute(
            provider=provider,
            model=model,
            messages=messages,
            api_key=api_key,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    elif provider == "claude":
        return await claude_adapter.execute(
            provider=provider,
            model=model,
            messages=messages,
            api_key=api_key,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    elif provider == "gemini":
        return await gemini_adapter.execute(
            provider=provider,
            model=model,
            messages=messages,
            api_key=api_key,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    else:
        raise ProviderError(f"Unknown provider: {provider}")
