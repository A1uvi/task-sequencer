import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_key() -> bytes:
    """Decode the base64-encoded 32-byte encryption key from settings."""
    return base64.b64decode(settings.encryption_key)


def encrypt_api_key(plaintext_key: str) -> str:
    """AES-256-GCM encrypt a plaintext API key string.

    Returns a base64-encoded string of: nonce (12 bytes) + ciphertext + tag.
    The AESGCM cipher appends the 16-byte authentication tag to the ciphertext
    automatically.
    """
    key_bytes = _get_key()
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_key.encode("utf-8"), None)
    combined = nonce + ciphertext_with_tag
    return base64.b64encode(combined).decode("utf-8")


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an AES-256-GCM encrypted API key.

    Reverses encrypt_api_key. Must only be called inside the worker process.
    Never log, never return to client.
    """
    key_bytes = _get_key()
    aesgcm = AESGCM(key_bytes)
    combined = base64.b64decode(encrypted_key.encode("utf-8"))
    nonce = combined[:12]
    ciphertext_with_tag = combined[12:]
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    return plaintext_bytes.decode("utf-8")
