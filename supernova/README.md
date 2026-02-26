# SuperNova

Production-grade personal AI agent with persistent memory and autonomous cognition.

## Features

- **Durable Execution** — Process crashes resume from interrupted steps via PostgreSQL checkpointing
- **Observability** — Full tracing with input/output capture for every LLM call
- **Security** — Capability-gated tool execution with human-in-the-loop approval
- **Self-Improvement** — Automatic skill crystallization from execution traces
- **Multi-Tier Memory** — Episodic (Neo4j), Semantic (PostgreSQL), Working (Redis)

## Installation

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
