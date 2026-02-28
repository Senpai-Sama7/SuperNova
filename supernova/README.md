# SuperNova

Production-grade personal AI agent with persistent memory and autonomous cognition.

## Features

- **Durable Execution** — Process crashes resume from interrupted steps via PostgreSQL checkpointing
- **Observability** — Full tracing with input/output capture for every LLM call
- **Security** — Capability-gated tool execution with human-in-the-loop approval
- **Self-Improvement** — Automatic skill crystallization from execution traces
- **Multi-Tier Memory** — Episodic (Neo4j), Semantic (PostgreSQL), Working (Redis)

## Installation

| Setup Type | Time | Requirements |
|------------|------|-------------|
| Minimal (local LLM only) | ~5 min | Python 3.12+, Ollama |
| Standard (with memory) | ~15 min | + Neo4j, Redis |
| Full (all features) | ~30 min | + API keys, Docker |

```bash
pip install -e ".[dev]"
```

## Development

```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy supernova
```

## License

MIT

## Local Model Fallback (Ollama)

SuperNova can fall back to local LLMs via [Ollama](https://ollama.com) when API budgets are exceeded or for privacy-sensitive tasks.

### Setup

```bash
# Install Ollama (macOS)
brew install ollama

# Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the default model
ollama pull llama3.2:3b

# Start the server
ollama serve
```

### Configuration

Set these in `.env`:

```bash
OLLAMA_ENABLED=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:3b
LOCAL_MODEL_PRIORITY=false   # set true to prefer local over cloud
```

When `LOCAL_MODEL_PRIORITY=false` (default), local models are used only as a budget fallback. When `true`, the router prefers local models for all tasks.

## Minimal Mode

Run SuperNova with ONLY Ollama (no external services):

```bash
# Install and start Ollama
ollama serve &
ollama pull llama3.2:3b

# Set minimal configuration
export OLLAMA_ENABLED=true
export LOCAL_MODEL_PRIORITY=true
export MEMORY_BACKEND=none
export CELERY_ENABLED=false

# Install and run
pip install -e .
supernova
```

**Available Features:**
- Basic agent functionality
- Local LLM inference
- Simple conversation

**Unavailable Features:**
- Persistent memory (Neo4j/PostgreSQL)
- Background tasks (Celery)
- Observability (Langfuse)
- Multi-session state

## Backup & Recovery

SuperNova includes automated backup and restore for all storage backends.

### Local Backups

Backups are enabled by default and run daily at 2:30 AM UTC via Celery Beat.

```bash
# Manual backup
python -m supernova.core.backup.cli backup --name "pre-update"

# List backups
python -m supernova.core.backup.cli backup --list

# Restore from local file
python -m supernova.core.backup.cli restore --from backups/backup_20260226.tar.gz
```

### Cloud Backup (S3-Compatible)

Supports AWS S3, Google Cloud Storage, MinIO, and Backblaze B2.

```bash
# .env configuration
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_PREFIX=supernova/

# For AWS S3
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1

# For MinIO / S3-compatible
export AWS_ENDPOINT_URL=http://localhost:9000

# For GCS (via S3 interop)
export AWS_ENDPOINT_URL=https://storage.googleapis.com
```

Restore from cloud:

```bash
python -m supernova.core.backup.cli restore --from s3://your-bucket/supernova/backup_20260226.tar.gz
```

### Backup Encryption

Set `BACKUP_ENCRYPTION_KEY` to a Fernet key to encrypt backups at rest:

```bash
# Generate a key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
BACKUP_ENCRYPTION_KEY=your-fernet-key-here
```

### Rotation Policy

Automated rotation keeps 7 daily + 4 weekly + 12 monthly backups (23 total max). Older backups are deleted automatically after each daily run.

## Secrets Management

SuperNova includes an encrypted secrets vault for API keys and sensitive configuration.

### Setup

```bash
# Initialize vault with master password
python3 -c "
from infrastructure.security.secrets import SecretsVault
vault = SecretsVault()
vault.unlock('your-master-password')
vault.store('OPENAI_API_KEY', 'sk-...')
print('Vault initialized')
"
```

### Platform Keychain

The master password can be stored in your OS keychain:
- **macOS**: Keychain Access (`security` CLI)
- **Linux**: GNOME Keyring / KDE Wallet (`secret-tool`)
- **Windows**: Credential Manager (`cmdkey`)

### Migration from Environment Variables

```bash
python3 -c "
from infrastructure.security.secrets import SecretsVault, migrate_env_to_vault
vault = SecretsVault()
vault.unlock('your-master-password')
results = migrate_env_to_vault(vault, ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY'])
print(results)
"
```

## Security Hardening

### Secure Serialization
Procedural memory uses HMAC-SHA256 signed pickle with a restricted unpickler that only allows `langgraph.*`, `langchain_core.*`, and Python builtins. Set `PICKLE_HMAC_KEY` to a strong random value in production.

### Audit Logging
All privileged operations are logged to the `audit_logs` table. Query via `GET /admin/audit-logs`.

### Sandbox Hardening
Code execution uses Docker with: `--network none`, `--read-only`, `--pids-limit 64`, `--tmpfs /tmp`, `--security-opt no-new-privileges`, and a seccomp profile blocking dangerous syscalls. Set `CODE_SANDBOX=gvisor` for gVisor runtime isolation.
