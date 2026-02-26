"""Secrets management with AES-256-GCM encryption and platform keychain support.

Provides encrypted-at-rest storage for API keys and sensitive configuration,
with optional platform keychain integration for the master key.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

_NONCE_LEN = 12  # 96-bit nonce for AES-GCM
_KEY_LEN = 32    # 256-bit key
_SALT_LEN = 16


class SecretsError(Exception):
    """Raised on secrets management failures."""


def _derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive AES-256 key from master password via PBKDF2-SHA256 (100k rounds)."""
    return hashlib.pbkdf2_hmac("sha256", master_password.encode(), salt, 100_000, dklen=_KEY_LEN)


class SecretsVault:
    """Encrypted secrets store backed by a local JSON file."""

    def __init__(self, vault_path: Path | None = None) -> None:
        self._path = vault_path or Path("./secrets.vault.json")
        self._key: bytes | None = None

    def unlock(self, master_password: str) -> None:
        """Derive encryption key from master password."""
        data = self._read_vault()
        salt = base64.b64decode(data.get("salt", "")) if data.get("salt") else os.urandom(_SALT_LEN)
        self._key = _derive_key(master_password, salt)
        if not data.get("salt"):
            self._write_vault({"salt": base64.b64encode(salt).decode(), "secrets": {}})

    def store(self, name: str, value: str) -> None:
        """Encrypt and store a secret."""
        if not self._key:
            raise SecretsError("Vault is locked — call unlock() first")
        nonce = os.urandom(_NONCE_LEN)
        ct = AESGCM(self._key).encrypt(nonce, value.encode(), name.encode())
        blob = base64.b64encode(nonce + ct).decode()
        data = self._read_vault()
        data.setdefault("secrets", {})[name] = blob
        self._write_vault(data)

    def retrieve(self, name: str) -> str:
        """Decrypt and return a secret."""
        if not self._key:
            raise SecretsError("Vault is locked — call unlock() first")
        data = self._read_vault()
        blob = data.get("secrets", {}).get(name)
        if not blob:
            raise SecretsError(f"Secret '{name}' not found")
        raw = base64.b64decode(blob)
        nonce, ct = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
        try:
            return AESGCM(self._key).decrypt(nonce, ct, name.encode()).decode()
        except Exception as exc:
            raise SecretsError(f"Decryption failed for '{name}' — wrong master password?") from exc

    def list_secrets(self) -> list[str]:
        """Return names of stored secrets (not values)."""
        return list(self._read_vault().get("secrets", {}).keys())

    def delete(self, name: str) -> None:
        """Remove a secret from the vault."""
        data = self._read_vault()
        data.get("secrets", {}).pop(name, None)
        self._write_vault(data)

    def _read_vault(self) -> dict[str, Any]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def _write_vault(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))


# ── Platform keychain helpers ────────────────────────────────────────────────

def keychain_store(service: str, account: str, password: str) -> bool:
    """Store master password in platform keychain. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(
                ["security", "add-generic-password", "-U",
                 "-s", service, "-a", account, "-w", password],
                check=True, capture_output=True,
            )
        elif system == "Linux":
            subprocess.run(
                ["secret-tool", "store", "--label", service,
                 "service", service, "account", account],
                input=password.encode(), check=True, capture_output=True,
            )
        elif system == "Windows":
            # Use cmdkey for Windows Credential Manager
            subprocess.run(
                ["cmdkey", f"/generic:{service}", f"/user:{account}", f"/pass:{password}"],
                check=True, capture_output=True,
            )
        else:
            return False
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Keychain storage unavailable on %s", system)
        return False


def keychain_retrieve(service: str, account: str) -> str | None:
    """Retrieve master password from platform keychain."""
    system = platform.system()
    try:
        if system == "Darwin":
            r = subprocess.run(
                ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
                check=True, capture_output=True, text=True,
            )
            return r.stdout.strip()
        elif system == "Linux":
            r = subprocess.run(
                ["secret-tool", "lookup", "service", service, "account", account],
                check=True, capture_output=True, text=True,
            )
            return r.stdout.strip()
        elif system == "Windows":
            # cmdkey doesn't support retrieval; use powershell
            cmd = (
                f"(Get-StoredCredential -Target '{service}').GetNetworkCredential().Password"
            )
            r = subprocess.run(
                ["powershell", "-Command", cmd],
                check=True, capture_output=True, text=True,
            )
            return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def migrate_env_to_vault(vault: SecretsVault, env_keys: list[str]) -> dict[str, str]:
    """Migrate secrets from environment variables into the vault.

    Returns mapping of migrated key names to status.
    """
    results: dict[str, str] = {}
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            vault.store(key, value)
            results[key] = "migrated"
        else:
            results[key] = "not_set"
    return results
