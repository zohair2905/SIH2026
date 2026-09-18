"""Password hashing and opaque session-token primitives for the API.

Passwords: scrypt via the standard library (salt + params stored with the
hash). Session tokens: 256-bit random values stored as SHA-256 digests so a
database leak does not expose live bearer tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_SCRYPT_N = 1 << 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DK_LEN = 32
_PREFIX = "scrypt"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_DK_LEN,
    )
    return f"{_PREFIX}:{_SCRYPT_N}:{_SCRYPT_R}:{_SCRYPT_P}:{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored.split(":")
        if scheme != _PREFIX:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=len(expected),
    )
    return hmac.compare_digest(digest, expected)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()