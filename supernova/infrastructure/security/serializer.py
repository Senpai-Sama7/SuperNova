"""Secure serialization with HMAC signing to replace raw pickle.

Wraps pickle with HMAC-SHA256 signing so that tampered or externally-supplied
blobs are rejected before deserialization ever occurs. This mitigates the
known RCE vector in pickle.loads() for the procedural memory store.

Wire format: HMAC(32 bytes) || pickled_data
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import pickle
from typing import Any

logger = logging.getLogger(__name__)

_HMAC_DIGEST = hashlib.sha256
_HMAC_LEN = 32  # SHA-256 digest length

# Types allowed during deserialization (module, qualname) prefixes
_ALLOWED_MODULE_PREFIXES = (
    "langgraph.",
    "langchain_core.",
    "builtins",
    "collections",
    "typing",
    "operator",
    "copyreg",
    "functools",
    "_operator",
)


class SerializationError(Exception):
    """Raised when serialization or deserialization fails."""


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickler that rejects types outside the allowlist."""

    def find_class(self, module: str, name: str) -> Any:
        if any(module.startswith(prefix) for prefix in _ALLOWED_MODULE_PREFIXES):
            return super().find_class(module, name)
        raise SerializationError(
            f"Blocked deserialization of {module}.{name} — not in allowlist"
        )


def secure_dumps(obj: Any, hmac_key: str) -> bytes:
    """Serialize obj with pickle and prepend HMAC signature."""
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sig = hmac.new(hmac_key.encode(), data, _HMAC_DIGEST).digest()
    return sig + data


def secure_loads(signed_data: bytes, hmac_key: str) -> Any:
    """Verify HMAC then deserialize with restricted unpickler."""
    if len(signed_data) < _HMAC_LEN:
        raise SerializationError("Data too short — missing HMAC signature")

    sig_received = signed_data[:_HMAC_LEN]
    payload = signed_data[_HMAC_LEN:]

    sig_expected = hmac.new(hmac_key.encode(), payload, _HMAC_DIGEST).digest()
    if not hmac.compare_digest(sig_received, sig_expected):
        raise SerializationError("HMAC verification failed — data may be tampered")

    import io
    return _RestrictedUnpickler(io.BytesIO(payload)).load()
