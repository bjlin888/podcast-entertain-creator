"""Fernet-based encryption for user API keys stored at rest."""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.encryption_key:
            raise RuntimeError(
                "ENCRYPTION_KEY not configured. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(settings.encryption_key.encode())
    return _fernet


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key, return base64-encoded ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an API key from base64-encoded ciphertext."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
