# SuperNova — AI Coding Agent Reference

> **Project Type**: Python 3.12+ (backend), React/TypeScript (dashboard)  
> **Architecture**: LangGraph-based cognitive loop with multi-tier memory systems

---

## Quick Commands

### Python Backend (supernova/)

```bash
cd supernova

# Install dependencies
uv sync --all-extras

# Lint & Format
ruff check .           # Lint
ruff check . --fix     # Auto-fix
ruff format .          # Format

# Type check
mypy . --ignore-missing-imports

# Run all tests
pytest tests/ -v

# Run single test
pytest tests/test_auth.py::test_function_name -v
pytest tests/test_auth.py -k "test_pattern" -v

# Run with coverage threshold
pytest tests/ --cov=supernova --cov-fail-under=80

# Run without coverage (faster)
pytest tests/ -v --no-cov

# Run unit tests only
pytest tests/ -v -m "not integration"
```

### Frontend (dashboard/)

```bash
cd dashboard

npm install
npm run dev
npm run build

npm run lint
npm run type-check
npm run test:unit        # Vitest
npm run test:e2e         # Playwright
npm run test             # All tests

# Single test
npx vitest run testFile.test.ts
```

### Infrastructure

```bash
# Start services
docker compose up -d

# Run API
uvicorn api.gateway:app --reload --log-level debug

# Run Celery worker
celery -A workers worker --loglevel=debug
```

---

## Code Style Guidelines

### Python

**Formatting**: 4 spaces, double quotes, 100 char line length

**Imports** (use ruff auto-fix):
```python
# Standard library first, then third-party, then local
import os
import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from supernova.config import get_settings
from supernova.api.routes import agent
```

**Type Annotations** (strict mypy):
- All functions MUST have type annotations
- Use `Optional[X]` not `X | None` for compatibility
- Use `from typing import Literal` for enums

**Naming Conventions**:
- `snake_case` for functions/variables
- `PascalCase` for classes/types
- `CAPITAL_SNAKE` for constants
- Prefix private methods with `_`
- Use descriptive names: `get_user_by_id` not `get_u`

**Error Handling**:
```python
# Prefer explicit exception handling
try:
    result = await get_data()
except DataNotFoundError:
    raise HTTPException(status_code=404, detail="Data not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")

# Use custom exceptions for domain errors
class AgentError(Exception):
    pass
```

**Async/Await**:
- Use `asyncpg` for PostgreSQL, `redis.asyncio` for Redis
- Always `await` async functions, never block the event loop
- Use `asyncio.gather()` for parallel operations

**Pydantic Models**:
```python
class UserInput(BaseModel):
    name: str
    age: int
    email: Optional[str] = None
    
    model_config = ConfigDict(str_strip_whitespace=True)
```

### TypeScript/React

**Formatting**: ESLint + Prettier (VSCode will auto-format)

**Imports**:
```typescript
// React imports first
import { useState, useEffect } from 'react';

// Then external libraries
import { useQuery } from '@tanstack/react-query';

// Then local imports
import { Button } from '@/components/ui';

// Types
import type { User } from '@/types';
```

**Naming**:
- `camelCase` for variables/functions
- `PascalCase` for components
- `kebab-case` for file names
- Prefix interfaces with `I` (optional): `IUserProps`

**Components**:
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
}

export function Button({ label, onClick }: ButtonProps) {
  return <button onClick={onClick}>{label}</button>;
}
```

---

## Key Patterns

### API Routes
```python
router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

@router.post("/message")
async def send_message(request: MessageRequest) -> MessageResponse:
    # Validate input, call agent, return response
    pass
```

### Agent State
```python
class AgentState(TypedDict):
    messages: list[BaseMessage]
    session_id: str
    checkpoint_ns: str
```

### Memory Systems
- **Working**: Redis + msgpack for fast ephemeral storage
- **Semantic**: PostgreSQL + pgvector for facts
- **Episodic**: Neo4j + Graphiti for temporal events
- **Procedural**: PostgreSQL for compiled skills

---

## Important Files

| File | Purpose |
|------|---------|
| `loop.py` | Main LangGraph cognitive loop |
| `context_assembly.py` | Positional context optimization |
| `interrupts.py` | HITL interrupt coordinator |
| `procedural.py` | Skill crystallization |
| `api/gateway.py` | FastAPI entry point |
| `dashboard/src/NovaDashboard.tsx` | Main UI |

---

## Testing Notes

- Tests are in `supernova/tests/` (27 test files)
- Use pytest fixtures from `conftest.py`
- Mark integration tests with `@pytest.mark.integration`
- Frontend tests use Vitest + Playwright

---

*Last Updated: 2026-02-26*
