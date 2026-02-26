---
name: observability-monitoring
description: Instrumentation, logging, metrics, tracing, and alerting strategies for production systems. Use when adding observability to code, debugging production issues, setting up monitoring dashboards, configuring alerts, designing SLIs/SLOs/SLAs, or improving system reliability through better visibility.
---

# Observability & Monitoring

Building systems that are understandable in production.

## The Three Pillars

### 1. Logs (Events)

**What they tell you**: What happened, in detail.

**Best practices:**
- Use structured logging (JSON) over text
- Include correlation IDs across services
- Log at appropriate levels (debug, info, warn, error)
- Include context (user_id, request_id, trace_id)

```python
# Good
logger.info("payment_processed", 
    user_id=user.id,
    amount=amount,
    currency="USD",
    payment_method="card",
    duration_ms=elapsed,
    trace_id=trace_id
)

# Bad
logger.info(f"User {user.id} paid {amount}")
```

### 2. Metrics (Aggregates)

**What they tell you**: System health over time.

**Key metric types:**
- **Counters**: Events (requests, errors)
- **Gauges**: Point-in-time values (queue depth, memory)
- **Histograms**: Distributions (latency percentiles)
- **Summaries**: Client-calculated aggregations

**Golden signals** (monitor these first):
- Latency (response time)
- Traffic (requests/second)
- Errors (error rate)
- Saturation (resource utilization)

### 3. Traces (Flows)

**What they tell you**: Request path through the system.

**Essential for:**
- Distributed systems
- Latency analysis
- Dependency mapping
- Bottleneck identification

## Instrumentation Strategy

### What to Instrument

**Every service should emit:**

```python
# Request metrics
http_requests_total{method, path, status}
http_request_duration_seconds{method, path, quantile}

# Business metrics
payments_processed_total{status, currency}
payment_amount_sum{currency}

# Resource metrics
cpu_usage_percent
memory_usage_bytes
disk_io_read_bytes

# Custom metrics
active_sessions_gauge
queue_depth{queue_name}
```

### Where to Instrument

```
┌─────────────┐
│   Client    │── HTTP client metrics (latency, errors)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Load Balancer│── Traffic metrics
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   API Gateway │── Request rate, auth metrics
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Service   │── Business logic metrics
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │── Query performance, connection pool
└─────────────┘
```

Use scripts/instrumentation-checker.py to verify coverage:
```bash
python scripts/instrumentation-checker.py \
  --source src/ \
  --config instrumentation-rules.yaml
```

## Logging Standards

### Structured Log Schema

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "info",
  "service": "payment-service",
  "message": "payment_processed",
  "trace_id": "abc-123-def",
  "span_id": "span-456",
  "user_id": "user-789",
  "duration_ms": 245,
  "context": {
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "card"
  }
}
```

### Log Levels

| Level | Use When | Action Required |
|-------|----------|-----------------|
| DEBUG | Detailed troubleshooting | None |
| INFO | Normal operations | None |
| WARN | Unexpected but handled | Monitor |
| ERROR | Failed operations | Investigate |
| FATAL | System unusable | Immediate response |

### Sampling Strategy

For high-volume logs:
- **Error logs**: 100% (never sample)
- **Info logs**: 10% in production
- **Debug logs**: 0% in production (enable on-demand)
- **Traces**: 1-5% in production, 100% for specific requests

## Alerting Design

### Alerting Principles

1. **Actionable**: Every alert needs a response
2. **Relevant**: Page for symptoms, not causes
3. **Timely**: Detect before significant impact
4. **Precise**: Minimize false positives

### Alert Severity Levels

| Severity | Response Time | Examples |
|----------|--------------|----------|
| P0 (Critical) | Immediate | Service down, data loss, security breach |
| P1 (High) | 15 minutes | Elevated error rate, performance degradation |
| P2 (Medium) | 1 hour | Capacity warnings, minor functionality issues |
| P3 (Low) | 24 hours | Non-urgent improvements, low-severity bugs |

### Alert Conditions

**Good alerts (symptom-based):**
```
# High error rate
rate(http_requests_total{status=~"5.."}[5m]) > 0.01

# Slow responses
histogram_quantile(0.99, rate(http_request_duration_bucket[5m])) > 2

# Low success rate
rate(payments_successful[5m]) / rate(payments_total[5m]) < 0.95
```

**Bad alerts (cause-based):**
```
# CPU usage (symptom, not problem)
cpu_usage_percent > 80

# Instead, alert on:
# - Slow response times
# - Failed requests
# - Queue buildup
```

### Alert Fatigue Prevention

```yaml
# Group related alerts
group_by: [service, severity]

# Prevent flapping
for: 5m  # Must be true for 5 minutes

# Auto-resolve
resolve_after: 10m

# Rate limiting
max_alerts_per_hour: 10
```

## SLI/SLO/SLA Framework

### Definitions

- **SLI (Service Level Indicator)**: Measurable metric
- **SLO (Service Level Objective)**: Target for SLI
- **SLA (Service Level Agreement)**: Contract with consequences

### Example

```yaml
service: payment-api
slis:
  availability:
    description: "Percentage of successful requests"
    calculation: "(total - errors) / total * 100"
    slo: 99.9%
    window: 30d
    
  latency:
    description: "Response time at 99th percentile"
    calculation: "histogram_quantile(0.99, response_time)"
    slo: < 500ms
    window: 30d
    
  error_rate:
    description: "Percentage of 5xx responses"
    calculation: "rate(5xx[5m]) / rate(total[5m]) * 100"
    slo: < 0.1%
    window: 30d
```

Use scripts/slo-calculator.py:
```bash
python scripts/slo-calculator.py \
  --metrics metrics.json \
  --slo-config slos.yaml \
  --output report.html
```

## Distributed Tracing

### Trace Context Propagation

```python
# Incoming request
trace_id = request.headers.get("X-Trace-ID") or generate_id()
span_id = generate_id()

# Outgoing request
headers = {
    "X-Trace-ID": trace_id,
    "X-Span-ID": span_id,
    "X-Sampled": "1"
}
response = requests.get(url, headers=headers)
```

### Span Attributes

```python
with tracer.start_span("process_payment") as span:
    span.set_attribute("user.id", user_id)
    span.set_attribute("payment.amount", amount)
    span.set_attribute("payment.currency", currency)
    span.set_attribute("payment.method", method)
    
    result = process_payment(...)
    
    span.set_attribute("payment.status", result.status)
    span.set_attribute("payment.duration_ms", elapsed)
```

### Sampling Strategies

- **Head-based**: Decision at trace start
- **Tail-based**: Decision after trace complete (catches slow traces)
- **Probabilistic**: Random sampling
- **Adaptive**: Dynamic based on volume

## Dashboard Design

### Dashboard Hierarchy

```
Executive Dashboard (5-minute view)
├── Service health (red/yellow/green)
├── Key business metrics
└── SLA compliance

Service Dashboard (15-minute view)
├── Golden signals
├── Error breakdown
├── Latency percentiles
└── Resource utilization

Detailed Dashboard (deep dive)
├── Request traces
├── Log exploration
├── Custom metrics
└── Correlations
```

### Key Dashboards to Build

1. **Service Overview**: Health at a glance
2. **Error Analysis**: Drill into failures
3. **Performance**: Latency distributions
4. **Capacity Planning**: Resource trends
5. **Business Metrics**: User-facing outcomes

## Incident Response

### Runbooks

Document common scenarios:

```markdown
# High Error Rate - Payment Service

## Detection
Alert: `payment_error_rate > 0.05`

## Investigation
1. Check recent deployments: `kubectl rollout history`
2. Review error logs: `kibana query`
3. Check dependency health: `dashboard link`

## Mitigation
1. If deployment caused: `kubectl rollout undo`
2. If dependency issue: Enable circuit breaker
3. If capacity: Scale up replicas

## Escalation
If not resolved in 15 minutes: Escalate to SRE team
```

Use scripts/runbook-generator.py:
```bash
python scripts/runbook-generator.py \
  --alerts alerts.yaml \
  --output runbooks/
```

## Resources

- [instrumentation-patterns.md](references/instrumentation-patterns.md) - Language-specific guides
- [alerting-rules.md](references/alerting-rules.md) - Common alert configurations
- [slo-examples.md](references/slo-examples.md) - SLO templates by service type
