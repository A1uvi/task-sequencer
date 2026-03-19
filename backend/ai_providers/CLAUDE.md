# ai_providers — AI Provider Abstraction Layer

## Purpose
Unified async interface for calling OpenAI, Anthropic Claude, and Google Gemini.
Zero dependency on the rest of the application — fully standalone module.

## Files
- `base.py` — ProviderMessage, ProviderResponse, QuotaExhaustedError, ProviderError, execute() stub
- `router.py` — top-level execute() that routes to correct adapter by provider string
- `openai_adapter.py` — OpenAI implementation
- `claude_adapter.py` — Anthropic implementation
- `gemini_adapter.py` — Google Gemini implementation
- `__init__.py` — exports execute, ProviderResponse, QuotaExhaustedError, ProviderError

## The Only Import the Worker Needs
```python
from ai_providers import execute, QuotaExhaustedError, ProviderError
```

## Adding a New Provider
1. Create `{provider}_adapter.py` implementing the `execute()` signature from `base.py`
2. Register it in `router.py`
3. Add a mock test in `tests/test_ai_providers.py`
No other files need to change.

## Error Handling Contract
- HTTP 429, `insufficient_quota`, `billing_limit_exceeded`, `resource_exhausted`
  → raise QuotaExhaustedError (the worker catches this to pause execution)
- All other provider errors → raise ProviderError with original message preserved

## system_prompt Handling
- OpenAI: inject as {"role": "system", "content": ...} at index 0 of messages
- Claude: pass as the `system=` parameter
- Gemini: prepend to first user message content

## Testing in Isolation
```bash
cd backend && pytest tests/test_ai_providers.py
```
All tests must mock HTTP — never make real API calls in tests.
