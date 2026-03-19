# app/core — Config, Security, Encryption

## Purpose
Cross-cutting infrastructure: environment config, JWT auth, AES-256 encryption.

## Files
- `config.py` — pydantic-settings Settings class. Single source of all env vars.
- `security.py` — JWT creation/validation, `get_current_user` FastAPI dependency.
- `encryption.py` — AES-256-GCM encrypt/decrypt for API keys.
- `database.py` — Async SQLAlchemy engine, AsyncSession factory, `get_db` dependency.

## Encryption Contract
`encrypt_api_key(plaintext: str) -> str`  — call before storing in DB
`decrypt_api_key(ciphertext: str) -> str` — call only inside worker, never in routes

## Critical Rules
- `decrypt_api_key` output must NEVER be logged, returned in a response, or stored
- `ENCRYPTION_KEY` must be a 32-byte base64-encoded secret from environment
- JWT secret comes from `SECRET_KEY` env var

## Testing encryption.py in isolation
```python
from app.core.encryption import encrypt_api_key, decrypt_api_key
ct = encrypt_api_key("sk-test-123")
assert decrypt_api_key(ct) == "sk-test-123"
```
