# SuperNova — Codebase Information

> Generated: 2026-02-26 | Commit: 1c51768 | Full analysis

## Project Identity

- **Name**: SuperNova
- **Version**: 2.0.0
- **License**: MIT
- **Python**: 3.12+
- **Description**: Production-grade personal AI agent with persistent memory and autonomous cognition

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Python source files | 93 |
| Python LOC (supernova/) | 11,366 |
| Root module LOC | 3,281 |
| Dashboard source files | 88 |
| Dashboard LOC (TSX/TS) | 11,111 |
| Test files | 27 |
| Git commits | 18 |
| Build phases | 16 |

## Languages & Frameworks

| Language | Usage | Framework |
|----------|-------|-----------|
| Python 3.12+ | Backend, agent core, API | FastAPI, LangGraph, Celery |
| TypeScript/TSX | Dashboard frontend | React 19, Vite 7, Three.js |
| SQL | Migrations | Alembic + asyncpg |
| Cypher | Episodic memory queries | Neo4j 5 |

## Repository Structure (Top-Level)

```
SuperNova/
├── loop.py                  # Cognitive loop (LangGraph StateGraph)
├── context_assembly.py      # Positional context window assembly
├── procedural.py            # Compiled skill storage & crystallization
├── dynamic_router.py        # Capability-vector model router
├── interrupts.py            # HITL interrupt coordinator
├── DEPLOYMENT.conf          # Systemd + Docker + Nginx config
├── docker-compose.yml       # Infrastructure stack
├── setup.sh                 # Environment setup script
├── PROGRESS_TRACKER.md      # 16-phase build tracker
├── SYSTEM_RELATION_GRAPH.md # Architecture knowledge graph
├── supernova/               # Main Python package
├── dashboard/               # React frontend
├── mcp_and_skills/          # MCP servers and skill definitions
├── workspace/               # Jailed file access directory
└── logs/                    # Application logs
```
