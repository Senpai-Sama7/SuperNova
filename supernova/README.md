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
