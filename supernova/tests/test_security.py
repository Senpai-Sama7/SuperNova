"""Tests for Phase 13: Security Hardening.

Covers secure serialization, secrets vault, audit logging, and sandbox hardening.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 13.1: Secure Serialization ───────────────────────────────────────────────

class TestSecureSerializer:
    """Tests for HMAC-signed serialization."""

    def test_roundtrip(self):
        from supernova.infrastructure.security.serializer import secure_dumps, secure_loads
        obj = {"key": "value", "nested": [1, 2, 3]}
        key = "test-hmac-key"
        blob = secure_dumps(obj, key)
        result = secure_loads(blob, key)
        assert result == obj

    def test_tampered_data_rejected(self):
        from supernova.infrastructure.security.serializer import (
            SerializationError, secure_dumps, secure_loads,
        )
        blob = secure_dumps("secret", "key1")
        tampered = blob[:16] + b"\xff" * 16 + blob[32:]
        with pytest.raises(SerializationError, match="HMAC verification failed"):
            secure_loads(tampered, "key1")

    def test_wrong_key_rejected(self):
        from supernova.infrastructure.security.serializer import (
            SerializationError, secure_dumps, secure_loads,
        )
        blob = secure_dumps([1, 2, 3], "correct-key")
        with pytest.raises(SerializationError, match="HMAC verification failed"):
            secure_loads(blob, "wrong-key")

    def test_truncated_data_rejected(self):
        from supernova.infrastructure.security.serializer import (
            SerializationError, secure_loads,
        )
        with pytest.raises(SerializationError, match="too short"):
            secure_loads(b"short", "key")

    def test_restricted_unpickler_blocks_os(self):
        """Verify that dangerous modules like os are blocked."""
        import io
        import pickle
        from supernova.infrastructure.security.serializer import (
            SerializationError, _RestrictedUnpickler,
        )
        # Craft a pickle that tries to call os.system
        payload = pickle.dumps(os.getcwd)
        with pytest.raises(SerializationError, match="not in allowlist"):
            _RestrictedUnpickler(io.BytesIO(payload)).load()

    def test_allowed_builtins_pass(self):
        from supernova.infrastructure.security.serializer import secure_dumps, secure_loads
        # dict, list, tuple, int, str are builtins — should pass
        obj = {"a": [1, (2, 3)], "b": "hello"}
        key = "k"
        assert secure_loads(secure_dumps(obj, key), key) == obj


class TestProceduralHMAC:
    """Verify procedural.py uses secure serialization."""

    def test_no_raw_pickle_import(self):
        """procedural.py must not import pickle directly."""
        src = Path(__file__).resolve().parent.parent.parent / "procedural.py"
        content = src.read_text()
        assert "import pickle" not in content
        assert "secure_dumps" in content
        assert "secure_loads" in content

    def test_skill_record_has_hmac_key(self):
        from supernova.core.memory.procedural import SkillRecord
        r = SkillRecord(
            id="x", name="t", description="d",
            trigger_conditions=[], compiled_graph_bytes=b"",
            trigger_embedding=[], hmac_key="k",
        )
        assert r.hmac_key == "k"


# ── 13.2: Secrets Management ─────────────────────────────────────────────────

class TestSecretsVault:
    """Tests for AES-256-GCM encrypted secrets vault."""

    def test_store_and_retrieve(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsVault
        vault = SecretsVault(tmp_path / "test.vault.json")
        vault.unlock("master-password")
        vault.store("API_KEY", "sk-secret-123")
        assert vault.retrieve("API_KEY") == "sk-secret-123"

    def test_wrong_password_fails(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsError, SecretsVault
        vault = SecretsVault(tmp_path / "test.vault.json")
        vault.unlock("correct-password")
        vault.store("KEY", "value")
        # New vault instance with wrong password
        vault2 = SecretsVault(tmp_path / "test.vault.json")
        vault2.unlock("wrong-password")
        with pytest.raises(SecretsError, match="Decryption failed"):
            vault2.retrieve("KEY")

    def test_missing_secret_raises(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsError, SecretsVault
        vault = SecretsVault(tmp_path / "test.vault.json")
        vault.unlock("pw")
        with pytest.raises(SecretsError, match="not found"):
            vault.retrieve("NONEXISTENT")

    def test_locked_vault_raises(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsError, SecretsVault
        vault = SecretsVault(tmp_path / "test.vault.json")
        with pytest.raises(SecretsError, match="locked"):
            vault.store("K", "V")

    def test_list_and_delete(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsVault
        vault = SecretsVault(tmp_path / "test.vault.json")
        vault.unlock("pw")
        vault.store("A", "1")
        vault.store("B", "2")
        assert set(vault.list_secrets()) == {"A", "B"}
        vault.delete("A")
        assert vault.list_secrets() == ["B"]

    def test_migrate_env_to_vault(self, tmp_path):
        from supernova.infrastructure.security.secrets import SecretsVault, migrate_env_to_vault
        vault = SecretsVault(tmp_path / "test.vault.json")
        vault.unlock("pw")
        with patch.dict(os.environ, {"MY_KEY": "my_val", "EMPTY": ""}):
            results = migrate_env_to_vault(vault, ["MY_KEY", "EMPTY", "MISSING"])
        assert results["MY_KEY"] == "migrated"
        assert results["EMPTY"] == "not_set"
        assert results["MISSING"] == "not_set"
        assert vault.retrieve("MY_KEY") == "my_val"


class TestKeychainHelpers:
    """Test keychain functions handle missing tools gracefully."""

    def test_keychain_store_unavailable(self):
        from supernova.infrastructure.security.secrets import keychain_store
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert keychain_store("svc", "acct", "pw") is False

    def test_keychain_retrieve_unavailable(self):
        from supernova.infrastructure.security.secrets import keychain_retrieve
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert keychain_retrieve("svc", "acct") is None


# ── 13.3: Audit Logging ──────────────────────────────────────────────────────

class TestAuditDecorator:
    """Tests for @audit_log decorator."""

    @pytest.mark.asyncio
    async def test_decorator_records_entry(self):
        from supernova.infrastructure.security.audit import _audit_buffer, audit_log

        _audit_buffer.clear()

        @audit_log("test.action", resource="test-resource")
        async def my_func(user_id: str = "u1"):
            return "ok"

        result = await my_func(user_id="user-42")
        assert result == "ok"
        assert len(_audit_buffer) == 1
        assert _audit_buffer[0]["action"] == "test.action"
        assert _audit_buffer[0]["user_id"] == "user-42"
        assert _audit_buffer[0]["resource"] == "test-resource"

    @pytest.mark.asyncio
    async def test_flush_buffer(self):
        from supernova.infrastructure.security.audit import (
            _audit_buffer, flush_audit_buffer, write_audit_entry,
        )

        _audit_buffer.clear()
        _audit_buffer.append({
            "user_id": "u1", "action": "x", "resource": "r", "details": {}, "ip_address": None,
        })

        with patch("supernova.infrastructure.security.audit.write_audit_entry", new_callable=AsyncMock) as mock_write:
            count = await flush_audit_buffer(MagicMock())
            assert count == 1
            assert len(_audit_buffer) == 0
            mock_write.assert_called_once()


class TestAuditEndpoint:
    """Test GET /admin/audit-logs endpoint."""

    def test_audit_logs_no_pool(self):
        from supernova.api.auth import get_current_user
        from supernova.api.gateway import app
        from starlette.testclient import TestClient

        app.dependency_overrides[get_current_user] = lambda: "test-user"
        client = TestClient(app)
        resp = client.get("/admin/audit-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        app.dependency_overrides.clear()


class TestAuditMigration:
    """Verify audit_logs migration file structure."""

    def test_migration_exists(self):
        mig = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "b7c3e9f12a45_audit_logs.py"
        assert mig.exists()
        content = mig.read_text()
        assert "supernova_audit_logs" in content
        assert "user_id" in content
        assert "action" in content
        assert "ip_address" in content
        assert "ix_sn_audit_logs_timestamp" in content


# ── 13.4: Enhanced Sandboxing ─────────────────────────────────────────────────

class TestSandboxHardening:
    """Tests for hardened code_exec."""

    def test_seccomp_policy_structure(self):
        from supernova.infrastructure.tools.builtin.code_exec import _SECCOMP_POLICY
        assert _SECCOMP_POLICY["defaultAction"] == "SCMP_ACT_ALLOW"
        blocked = _SECCOMP_POLICY["syscalls"][0]["names"]
        assert "ptrace" in blocked
        assert "mount" in blocked
        assert "reboot" in blocked

    def test_docker_args_default(self):
        from supernova.infrastructure.tools.builtin.code_exec import _build_docker_args
        args = _build_docker_args("/tmp/test.py")
        assert "--network" in args
        assert "none" in args
        assert "--read-only" in args
        assert "--pids-limit" in args
        assert "no-new-privileges" in " ".join(args)
        assert "--tmpfs" in args

    def test_docker_args_gvisor(self):
        from supernova.infrastructure.tools.builtin.code_exec import _build_docker_args
        args = _build_docker_args("/tmp/test.py", sandbox_type="gvisor")
        assert "--runtime" in args
        assert "runsc" in args

    def test_docker_args_seccomp(self):
        from supernova.infrastructure.tools.builtin.code_exec import _build_docker_args
        args = _build_docker_args("/tmp/test.py", seccomp_path="/tmp/seccomp.json")
        joined = " ".join(args)
        assert "seccomp=/tmp/seccomp.json" in joined

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        result = await _code_exec("console.log('hi')", language="javascript")
        assert result["exit_code"] == 1
        assert "Unsupported" in result["stderr"]

    @pytest.mark.asyncio
    async def test_subprocess_fallback(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # First call (docker) raises FileNotFoundError, second call (subprocess) works
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
            mock_proc.returncode = 0
            mock_exec.side_effect = [FileNotFoundError, mock_proc]

            result = await _code_exec("print('hello')")
            assert result["sandbox"] == "subprocess"
            assert result["stdout"] == "hello\n"
