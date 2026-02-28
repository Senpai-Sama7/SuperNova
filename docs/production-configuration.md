# Production Configuration Guardrails

This repository now includes a deployment-time validator at:

- `scripts/validate_production_env.py`

## What it checks

When `SUPERNOVA_ENV=production`, the validator rejects:
- placeholder or template values for required secrets
- development defaults for database, Neo4j, and encryption-related keys
- `localhost` / `127.0.0.1` CORS origins
- `CODE_SANDBOX=none`

## Run before deploy

```bash
SUPERNOVA_ENV=production python scripts/validate_production_env.py
```

## Recommended deployment gate

Run this validator in your deployment pipeline before starting the API or workers.

That gives SuperNova an enforceable preflight check even before the deeper runtime config integration lands.
