# API Authentication Gap Analysis — Task 17.1.1

**Generated:** 2026-02-28T09:52 CST

## Currently Protected Endpoints (7)

| Endpoint | File | Line |
|----------|------|------|
| `GET /memory/semantic` | gateway.py | 437 |
| `GET /admin/audit-logs` | gateway.py | 481 |
| `GET /memory/export` | gateway.py | 503 |
| `POST /memory/import` | gateway.py | 539 |
| `POST /mcp/tools/{tool_name}` | mcp_routes.py | 54 |
| `POST /skills/{name}/activate` | mcp_routes.py | 88 |
| `POST /skills/{name}/deactivate` | mcp_routes.py | 101 |

## UNPROTECTED Endpoints (19) — Need Auth

| Endpoint | File | Line | Severity |
|----------|------|------|----------|
| `GET /metrics` | gateway.py | 366 | Medium |
| `GET /memory/procedural` | gateway.py | 451 | 🔴 High |
| `GET /admin/fleet` | gateway.py | 463 | 🔴 High |
| `GET /admin/costs` | gateway.py | 472 | 🔴 High |
| `GET /preferences` | preferences.py | 161 | 🔴 High |
| `POST /preferences` | preferences.py | 181 | 🔴 High |
| `POST /preferences/preset/{name}` | preferences.py | 209 | Medium |
| `GET /preferences/presets` | preferences.py | 225 | Low |
| `GET /preferences/options` | preferences.py | 231 | Low |
| `GET /dashboard/snapshot` | dashboard.py | 192 | Medium |
| `POST /approvals/{id}/resolve` | dashboard.py | 573 | 🔴 Critical |
| `GET /onboarding/status` | onboarding.py | 36 | Low |
| `POST /onboarding/validate-key` | onboarding.py | 46 | Medium |
| `GET /onboarding/cost-estimate` | onboarding.py | 66 | Low |
| `POST /onboarding/complete` | onboarding.py | 79 | Medium |
| `POST /agent/message` | agent.py | 26 | 🔴 Critical |
| `GET /mcp/servers` | mcp_routes.py | 34 | Medium |
| `GET /mcp/tools` | mcp_routes.py | 42 | Medium |
| `GET /skills` | mcp_routes.py | 80 | Low |

## Endpoints That Should Stay Public

| Endpoint | Reason |
|----------|--------|
| `GET /health` | Health check (load balancers) |
| `GET /health/deep` | Deep health check |
| `GET /healthz` | K8s liveness probe |
| `POST /auth/token` | Login endpoint (issues tokens) |

## Critical Findings

- `POST /agent/message` is **completely unprotected** — anyone can send messages to the agent
- `POST /approvals/{id}/resolve` is **completely unprotected** — anyone can approve/deny actions
- All `/admin/*` endpoints expose fleet and cost data without auth
- All `/preferences` endpoints allow reading/writing user preferences without auth

## Recommended Fix

Add `user_id: str = Depends(get_current_user)` to each unprotected endpoint's function signature. The `get_current_user` dependency already exists and handles JWT validation.
