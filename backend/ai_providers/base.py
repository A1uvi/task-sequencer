from dataclasses import dataclass, field
from typing import Any


@dataclass
class MessageAttachment:
    filename: str
    content_type: str   # "image/jpeg", "image/png", "text/plain", etc.
    data: str           # base64-encoded bytes


@dataclass
class ProviderMessage:
    role: str          # "user" | "assistant" | "system"
    content: str
    attachments: list[MessageAttachment] = field(default_factory=list)


@dataclass
class ProviderResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw_response: dict[str, Any]


class QuotaExhaustedError(Exception):
    """Raised on 429 / quota errors. Always catchable by the worker."""
    pass


class ProviderError(Exception):
    """Raised for all other non-recoverable provider errors."""
    pass


async def execute(
    provider: str,                        # "openai" | "claude" | "gemini"
    model: str,
    messages: list[ProviderMessage],
    api_key: str,                         # plaintext — decrypted before passing in
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs: Any
) -> ProviderResponse:
    """
    Stub execute function — actual routing is done in router.py.
    This module defines the interface contract only.
    """
    ...
