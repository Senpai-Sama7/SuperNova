"""Unit tests for supernova.infrastructure.security.serializer.

These tests validate the security contract:
- Wire format: HMAC(32 bytes) || pickled_data
- Tampering or wrong keys fail before deserialization
- Restricted unpickler blocks non-allowlisted modules

All tests are pure and require no network or external services.
"""

from __future__ import annotations

import os
import pickle

import pytest

from supernova.infrastructure.security.serializer import (
    SerializationError,
    secure_dumps,
    secure_loads,
)


class TestSecureSerializer:
    def test_round_trip_with_safe_builtins(self) -> None:
        obj = {
            "a": 1,
            "b": ["x", "y", 3],
            "c": (True, None, 4.5),
            "d": {"nested": {"k": "v"}},
        }
        blob = secure_dumps(obj, hmac_key="k")
        out = secure_loads(blob, hmac_key="k")
        assert out == obj

    def test_wire_format_has_hmac_prefix(self) -> None:
        obj = {"x": 1}
        blob = secure_dumps(obj, hmac_key="k")
        assert isinstance(blob, (bytes, bytearray))
        # SHA-256 digest length is 32 bytes (signature prefix)
        assert len(blob) > 32
        assert blob[:32] != b"" * 32

    def test_too_short_blob_raises(self) -> None:
        with pytest.raises(SerializationError, match=r"too short"):
            secure_loads(b"abc", hmac_key="k")

    def test_wrong_key_fails_hmac(self) -> None:
        blob = secure_dumps({"x": 1}, hmac_key="key1")
        with pytest.raises(SerializationError, match=r"HMAC verification failed"):
            secure_loads(blob, hmac_key="key2")

    def test_tampered_payload_fails_hmac(self) -> None:
        blob = bytearray(secure_dumps({"x": 1}, hmac_key="k"))
        # Flip one bit in payload section
        blob[-1] ^= 0x01
        with pytest.raises(SerializationError, match=r"HMAC verification failed"):
            secure_loads(bytes(blob), hmac_key="k")

    def test_tampered_signature_fails_hmac(self) -> None:
        blob = bytearray(secure_dumps({"x": 1}, hmac_key="k"))
        # Flip one bit in signature section
        blob[0] ^= 0x01
        with pytest.raises(SerializationError, match=r"HMAC verification failed"):
            secure_loads(bytes(blob), hmac_key="k")

    def test_restricted_unpickler_blocks_disallowed_module_global(self) -> None:
        """A pickle referencing os.system should be blocked by the allowlist."""

        class Evil:
            def __reduce__(self):
                return (os.system, ("echo should_not_run",))

        payload = pickle.dumps(Evil(), protocol=pickle.HIGHEST_PROTOCOL)
        signed = secure_dumps(payload, hmac_key="k")

        # secure_loads expects signed pickle of an object, not a pickle-bytes payload.
        # So we instead sign the Evil() object directly, ensuring HMAC passes first.
        signed2 = secure_dumps(Evil(), hmac_key="k")

        with pytest.raises(SerializationError, match=r"Blocked deserialization"):
            secure_loads(signed2, hmac_key="k")

    def test_restricted_unpickler_error_mentions_module_and_name(self) -> None:
        class Evil:
            def __reduce__(self):
                return (os.system, ("echo should_not_run",))

        signed = secure_dumps(Evil(), hmac_key="k")
        with pytest.raises(SerializationError) as ei:
            secure_loads(signed, hmac_key="k")
        msg = str(ei.value)
        assert "os" in msg or "posix" in msg or "nt" in msg
        assert "system" in msg
