"""Tests for TrustedContext and TrustLevel (supernova/core/security/trusted_context.py).

ToT paths covered:
  G  unauthenticated() factory mints GUEST-level context with empty user_id
  H  from_jwt_claims() maps role claims to TrustLevel; unknown role → USER
  I  can_execute_tool() grants access by level OR by pre-approval bypass
  J  fingerprint() returns a 16-character hex digest, unique per identity
  K  is_expired() correctly detects stale contexts using configurable TTL
"""
from __future__ import annotations

import time

from supernova.core.security.trusted_context import TrustedContext, TrustLevel


# ---------------------------------------------------------------------------
# Path G: unauthenticated() factory
# ---------------------------------------------------------------------------

def test_unauthenticated_factory_produces_guest_level() -> None:
    ctx = TrustedContext.unauthenticated(session_id="anon-001", ip_address="1.2.3.4")

    assert ctx.trust_level == TrustLevel.GUEST
    assert ctx.user_id == ""
    assert ctx.session_id == "anon-001"
    assert ctx.ip_address == "1.2.3.4"
    assert len(ctx.approved_tool_ids) == 0


# ---------------------------------------------------------------------------
# Path H: from_jwt_claims() role mapping
# ---------------------------------------------------------------------------

def test_from_jwt_claims_maps_known_roles() -> None:
    role_to_level = {
        "system": TrustLevel.SYSTEM,
        "admin": TrustLevel.ADMIN,
        "power_user": TrustLevel.POWER_USER,
        "user": TrustLevel.USER,
        "guest": TrustLevel.GUEST,
    }
    for role, expected in role_to_level.items():
        ctx = TrustedContext.from_jwt_claims(
            claims={"sub": "u1", "role": role},
            session_id="s1",
        )
        assert ctx.trust_level == expected, f"Failed for role={role!r}"


def test_from_jwt_claims_unknown_role_defaults_to_user() -> None:
    ctx = TrustedContext.from_jwt_claims(
        claims={"sub": "u99", "role": "super_secret_tier"},
        session_id="s2",
    )
    assert ctx.trust_level == TrustLevel.USER


def test_from_jwt_claims_missing_role_defaults_to_user() -> None:
    ctx = TrustedContext.from_jwt_claims(
        claims={"sub": "u100"},
        session_id="s3",
    )
    assert ctx.trust_level == TrustLevel.USER


def test_from_jwt_claims_populates_user_id_and_ip() -> None:
    ctx = TrustedContext.from_jwt_claims(
        claims={"sub": "alice", "role": "admin", "ip": "10.0.0.1"},
        session_id="s4",
        approved_tool_ids=frozenset({"safe_tool"}),
        trace_id="trace-xyz",
    )
    assert ctx.user_id == "alice"
    assert ctx.ip_address == "10.0.0.1"
    assert "safe_tool" in ctx.approved_tool_ids
    assert ctx.trace_id == "trace-xyz"


# ---------------------------------------------------------------------------
# Path I: can_execute_tool()
# ---------------------------------------------------------------------------

def test_can_execute_tool_by_sufficient_trust_level() -> None:
    ctx = TrustedContext(
        session_id="s", user_id="u", trust_level=TrustLevel.ADMIN
    )
    assert ctx.can_execute_tool("any_tool", required_level=TrustLevel.USER) is True
    assert ctx.can_execute_tool("any_tool", required_level=TrustLevel.ADMIN) is True


def test_can_execute_tool_denied_by_insufficient_level() -> None:
    ctx = TrustedContext(
        session_id="s", user_id="u", trust_level=TrustLevel.GUEST
    )
    assert ctx.can_execute_tool("bash_exec", required_level=TrustLevel.ADMIN) is False


def test_can_execute_tool_pre_approval_bypasses_level_requirement() -> None:
    # UNTRUSTED caller with tool explicitly pre-approved
    ctx = TrustedContext(
        session_id="s",
        user_id="u",
        trust_level=TrustLevel.UNTRUSTED,
        approved_tool_ids=frozenset({"special_tool"}),
    )
    # Would normally be denied (UNTRUSTED < ADMIN), but pre-approval overrides
    assert ctx.can_execute_tool("special_tool", required_level=TrustLevel.ADMIN) is True
    # Other tools still denied
    assert ctx.can_execute_tool("other_tool", required_level=TrustLevel.ADMIN) is False


# ---------------------------------------------------------------------------
# Path J: fingerprint()
# ---------------------------------------------------------------------------

def test_fingerprint_is_16_char_hex() -> None:
    ctx = TrustedContext.unauthenticated("fp-test")
    fp = ctx.fingerprint()

    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_differs_across_distinct_contexts() -> None:
    ctx_a = TrustedContext(session_id="s1", user_id="alice", trust_level=TrustLevel.USER)
    ctx_b = TrustedContext(session_id="s2", user_id="bob", trust_level=TrustLevel.ADMIN)

    assert ctx_a.fingerprint() != ctx_b.fingerprint()


# ---------------------------------------------------------------------------
# Path K: is_expired()
# ---------------------------------------------------------------------------

def test_is_expired_returns_false_for_fresh_context() -> None:
    ctx = TrustedContext(
        session_id="s",
        user_id="u",
        trust_level=TrustLevel.USER,
        created_at=time.time(),
    )
    assert ctx.is_expired(ttl_seconds=3600.0) is False


def test_is_expired_returns_true_for_stale_context() -> None:
    ctx = TrustedContext(
        session_id="s",
        user_id="u",
        trust_level=TrustLevel.USER,
        created_at=time.time() - 7200.0,  # 2 hours old
    )
    assert ctx.is_expired(ttl_seconds=3600.0) is True


def test_is_expired_respects_custom_ttl() -> None:
    ctx = TrustedContext(
        session_id="s",
        user_id="u",
        trust_level=TrustLevel.USER,
        created_at=time.time() - 500.0,
    )
    assert ctx.is_expired(ttl_seconds=600.0) is False   # 500s < 600s TTL
    assert ctx.is_expired(ttl_seconds=300.0) is True    # 500s > 300s TTL
