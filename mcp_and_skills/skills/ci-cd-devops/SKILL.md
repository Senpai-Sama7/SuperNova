---
name: ci-cd-devops
description: Continuous integration, continuous deployment, infrastructure as code, and DevOps practices for automated software delivery. Use when setting up CI/CD pipelines, designing deployment strategies, managing infrastructure, implementing GitOps, configuring build systems, or optimizing delivery workflows.
---

# CI/CD & DevOps

Automating the path from code commit to production.

## CI/CD Pipeline Design

### Pipeline Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Build   │───→│   Test   │───→│  Security│───→│  Staging │───→│Production│
│          │    │          │    │          │    │          │    │          │
│- Compile │    │- Unit    │    │- SAST    │    │- Deploy  │    │- Deploy  │
│- Package │    │- Integrat│    │- DAST    │    │- Smoke   │    │- Monitor │
│- Lint    │    │- Coverage│    │- Secrets │    │- E2E     │    │- Verify  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                │                │                │                │
   Fast            <10 min          <20 min          <30 min         Manual
   Feedback         Gate             Gate             Gate           or Auto
```

### Pipeline Principles

1. **Fail fast**: Run quick checks first
2. **Deterministic**: Same input = same output
3. **Hermetic**: No external dependencies
4. **Parallel**: Run independent jobs concurrently
5. **Idempotent**: Can re-run safely

## Build Systems

### Build Configuration

**Version everything:**
```yaml
# .github/workflows/build.yaml
name: Build
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18.17.0'
  PYTHON_VERSION: '3.11'

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          npm ci
          pip install -r requirements.txt
      
      - name: Lint
        run: |
          npm run lint
          ruff check src/
      
      - name: Test
        run: |
          npm test
          pytest --cov=src --cov-report=xml
      
      - name: Build
        run: npm run build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ github.sha }}
          path: dist/
```

### Build Optimization

**Speed up pipelines:**
- Cache dependencies (lock files as cache keys)
- Parallel test execution
- Incremental builds
- Build only changed components
- Use matrix builds for multiple versions

```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]
    os: [ubuntu-latest, windows-latest]
```

## Testing in CI

### Test Stages

```yaml
jobs:
  unit-tests:
    steps:
      - run: pytest tests/unit/ -x --tb=short
  
  integration-tests:
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
    steps:
      - run: pytest tests/integration/
  
  e2e-tests:
    needs: integration-tests
    steps:
      - run: npm run test:e2e
```

### Test Parallelization

```yaml
- name: Parallel Tests
  run: |
    pytest tests/ -n auto --dist=loadfile
```

## Deployment Strategies

### Basic Deployment

```
┌──────────┐
│  Build   │── Push image ──→┌──────────┐
│  Image   │                 │ Registry │
└──────────┘                 └────┬─────┘
                                  │ Pull
                                  ▼
                            ┌──────────┐
                            │  Server  │── Replace old version
                            └──────────┘
```

### Blue-Green Deployment

```
Active: Green        Switch        Active: Blue
┌────────┐         Traffic         ┌────────┐
│  Blue  │◄───────────────────────│  Green │
│ (old)  │                         │ (new)  │
└────────┘                         └────────┘
                                     ▲
                                     │ Deploy & Test
                                   Build
```

**Pros**: Instant rollback, zero downtime
**Cons**: Double infrastructure cost

### Canary Deployment

```
100%              90/10             50/50             0/100
┌─────┐          ┌─────┐           ┌─────┐           ┌─────┐
│Old  │    →     │Old  │     →     │Old  │     →     │New  │
│100% │          │90%  │           │50%  │           │100% │
└─────┘          └─────┘           └─────┘           └─────┘
                    ▲                 ▲
                    │                 │
                 ┌─────┐           ┌─────┐
                 │New  │           │New  │
                 │10%  │           │50%  │
                 └─────┘           └─────┘
```

**Pros**: Risk mitigation, gradual rollout
**Cons**: Complex traffic management

### Feature Flags

```python
if feature_flags.is_enabled("new-payment-flow", user_id):
    result = new_payment_process(data)
else:
    result = old_payment_process(data)
```

Deploy code dark, enable gradually.

## Infrastructure as Code

### Terraform Patterns

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

# environments/prod/main.tf
module "vpc" {
  source = "../../modules/vpc"
  
  environment = "production"
  vpc_cidr    = "10.0.0.0/16"
}
```

### State Management

- Remote state (S3, GCS, Azure Blob)
- State locking (DynamoDB, Consul)
- State encryption
- Separate state per environment

### GitOps with ArgoCD

```yaml
# application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Container Orchestration

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myapp/api:${IMAGE_TAG}
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Health Checks

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class HealthStatus(BaseModel):
    status: str
    version: str
    checks: dict

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(
        status="healthy",
        version="1.2.3",
        checks={
            "database": await check_database(),
            "cache": await check_cache(),
            "external_api": await check_external_api()
        }
    )
```

## Secrets Management

### Kubernetes Secrets

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
  - secretKey: database_url
    remoteRef:
      key: secret/data/app
      property: database_url
```

### CI/CD Secrets

Never commit secrets. Use:
- GitHub Secrets
- GitLab CI/CD Variables
- Azure DevOps Variable Groups
- Jenkins Credentials

## Monitoring Deployments

### Deployment Verification

```yaml
- name: Verify Deployment
  run: |
    kubectl rollout status deployment/api --timeout=5m
    
    # Smoke tests
    curl -f http://api/health
    
    # Check error rate
    scripts/check-error-rate.sh --threshold=0.01
```

### Automated Rollback

```bash
#!/bin/bash
# rollback-on-error.sh

ERROR_RATE=$(get_error_rate)
THRESHOLD=0.05

if (( $(echo "$ERROR_RATE > $THRESHOLD" | bc -l) )); then
  echo "Error rate $ERROR_RATE exceeds threshold $THRESHOLD. Rolling back..."
  kubectl rollout undo deployment/api
  exit 1
fi
```

## Environment Management

### Environment Promotion

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   Dev   │───→│   Test  │───→│  Stage  │───→│  Prod   │
│         │    │         │    │         │    │         │
│ Feature │    │  Full   │    │  Pre-   │    │  Live   │
│ branch  │    │  suite  │    │  prod   │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
   Auto           Auto          Manual        Manual
   deploy         deploy        gate          gate
```

### Configuration per Environment

```yaml
# config/production.yaml
database:
  pool_size: 20
  max_overflow: 10
  
cache:
  ttl: 3600
  
logging:
  level: INFO
  format: json
  
features:
  enable_cache: true
  enable_cdn: true
```

## Disaster Recovery

### Backup Strategy

```yaml
- name: Database Backup
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention:
    daily: 7
    weekly: 4
    monthly: 12
  
- name: State Backup
  schedule: "*/15 * * * *"  # Every 15 minutes
  storage: s3://backups/state/
```

### Recovery Procedures

Document in runbooks:
- Database restore from backup
- Full environment rebuild
- DNS failover
- Communication plan

## Tools and Scripts

Use scripts/pipeline-validator.py:
```bash
python scripts/pipeline-validator.py \
  --config .github/workflows/ \
  --rules pipeline-rules.yaml
```

Use scripts/deployment-checklist.py:
```bash
python scripts/deployment-checklist.py \
  --environment production \
  --version 1.2.3
```

## Resources

- [deployment-patterns.md](references/deployment-patterns.md) - Deployment strategies
- [iac-patterns.md](references/iac-patterns.md) - Infrastructure as code
- [kubernetes-patterns.md](references/kubernetes-patterns.md) - K8s best practices
