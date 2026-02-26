---
name: security-engineering
description: Secure coding practices, vulnerability assessment, threat modeling, and security hardening for software systems. Use when writing security-sensitive code, reviewing for vulnerabilities, implementing authentication/authorization, handling sensitive data, performing security audits, or designing secure architectures.
---

# Security Engineering

Building secure systems through defense in depth.

## Security Principles

1. **Defense in depth**: Multiple layers of security
2. **Least privilege**: Minimum access required
3. **Fail secure**: Default to safe state on failure
4. **Never trust input**: Validate everything
5. **Security by design**: Build in from start, not bolt on
6. **Assume breach**: Plan for compromise

## Secure Development Lifecycle

### Phase 1: Requirements

**Security requirements checklist:**
- [ ] Authentication method defined (OAuth, SAML, etc.)
- [ ] Authorization model specified (RBAC, ABAC)
- [ ] Data classification identified (PII, PHI, financial)
- [ ] Compliance requirements noted (GDPR, HIPAA, SOC2)
- [ ] Threat model started

### Phase 2: Design

**Threat Modeling (STRIDE):**

| Threat | Question | Mitigation |
|--------|----------|------------|
| Spoofing | Can someone pretend to be another user? | Authentication, MFA |
| Tampering | Can data be modified? | Integrity checks, signatures |
| Repudiation | Can actions be denied? | Audit logging |
| Info Disclosure | Can unauthorized data be seen? | Encryption, access controls |
| Denial of Service | Can service be overwhelmed? | Rate limiting, throttling |
| Elevation | Can privileges be increased? | Authorization checks |

Use scripts/threat-model.py:
```bash
python scripts/threat-model.py \
  --diagram architecture.png \
  --output threats.md
```

### Phase 3: Implementation

See language-specific secure coding guides in [secure-coding/](references/secure-coding/).

### Phase 4: Verification

**Security testing:**
```bash
# Static analysis
bandit -r src/
semgrep --config=auto src/

# Dependency scanning
safety check
npm audit

# Container scanning
trivy image myapp:latest

# Dynamic testing
zap-api-scan.py -t http://api:8080
```

### Phase 5: Deployment

**Hardening checklist:**
- [ ] Secrets in vault (not env vars)
- [ ] TLS everywhere
- [ ] Network policies configured
- [ ] Logging enabled
- [ ] Monitoring/alerting active

## Input Validation

### Validation Layers

```
Client (UX) → API Gateway → Service → Database
   ↓               ↓           ↓          ↓
Format         Schema      Business   Constraints
```

### Validation Rules

**Whitelist over blacklist:**
```python
# Good - whitelist allowed characters
if not re.match(r'^[a-zA-Z0-9_]+$', username):
    raise ValidationError()

# Bad - blacklist specific characters
if '<' in username or '>' in username:  # Missing others!
    raise ValidationError()
```

**Type safety:**
```python
from pydantic import BaseModel, validator

class PaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(pattern='^[A-Z]{3}$')
    card_token: str = Field(min_length=10, max_length=50)
    
    @validator('currency')
    def valid_currency(cls, v):
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError('Unsupported currency')
        return v
```

## Authentication

### Password Security

```python
import bcrypt

# Hashing
password_hash = bcrypt.hashpw(
    password.encode(), 
    bcrypt.gensalt(rounds=12)
)

# Verification
if bcrypt.checkpw(password.encode(), stored_hash):
    # Authenticated
```

**Requirements:**
- Min 12 characters
- No complexity requirements (length > complexity)
- Check against breach databases (Have I Been Pwned)
- Rate limit attempts (exponential backoff)

### Token Security

**JWT best practices:**
```python
import jwt

# Signing
token = jwt.encode(
    payload={
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "jti": generate_unique_id()  # For revocation
    },
    key=private_key,
    algorithm="ES256"  # Avoid HS256 for distributed systems
)

# Verification
try:
    payload = jwt.decode(
        token,
        key=public_key,
        algorithms=["ES256"],
        audience="my-api",
        issuer="auth-service"
    )
except jwt.ExpiredSignatureError:
    # Handle expiration
    pass
```

**Token guidelines:**
- Short expiration (15-60 minutes)
- Refresh token rotation
- Secure storage (httpOnly cookies)
- Binding to client (device fingerprint)

### OAuth 2.0 / OIDC

```python
# Authorization code flow
@app.get("/auth/callback")
async def auth_callback(code: str, state: str):
    # Verify state matches (CSRF protection)
    if state != stored_state:
        raise SecurityError()
    
    # Exchange code for tokens
    tokens = await exchange_code(code)
    
    # Validate ID token
    user_info = validate_id_token(tokens.id_token)
    
    # Create session
    session = create_session(user_info)
    
    return redirect(f"/app?session={session.id}")
```

## Authorization

### RBAC (Role-Based)

```python
@require_role("admin")
def delete_user(user_id: str):
    pass

@require_role(["editor", "admin"])
def update_post(post_id: str):
    pass
```

### ABAC (Attribute-Based)

```python
@require_permission(
    resource="document",
    action="write",
    condition=lambda user, doc: doc.owner_id == user.id
)
def edit_document(doc_id: str, content: str):
    pass
```

### Policy Enforcement Points

```python
# Middleware pattern
@app.middleware("http")
async def authorization(request, call_next):
    resource = request.path_params.get("resource_id")
    action = map_method_to_action(request.method)
    user = request.state.user
    
    if not authz.check(user, resource, action):
        raise HTTPException(403)
    
    return await call_next(request)
```

## Data Protection

### Encryption at Rest

```python
from cryptography.fernet import Fernet

# Key management via KMS
key = kms.get_data_key()
cipher = Fernet(key)

# Encrypt sensitive fields
encrypted_ssn = cipher.encrypt(ssn.encode())
```

### Encryption in Transit

**TLS requirements:**
- TLS 1.2 minimum (1.3 preferred)
- Strong cipher suites only
- Certificate pinning for mobile
- HSTS headers

### Secret Management

**Never:**
- Hardcode secrets in source
- Commit .env files
- Log secrets
- Pass secrets in URLs

**Always:**
- Use secret management service (Vault, AWS SM)
- Rotate secrets regularly
- Use short-lived credentials
- Audit secret access

## Common Vulnerabilities

### OWASP Top 10

1. **Broken Access Control**
   - Missing authorization checks
   - IDOR (Insecure Direct Object References)
   - CORS misconfiguration

2. **Cryptographic Failures**
   - Weak algorithms (MD5, SHA1)
   - Improper key management
   - Missing encryption

3. **Injection**
   - SQL injection
   - Command injection
   - NoSQL injection

4. **Insecure Design**
   - Missing security controls
   - Business logic flaws

5. **Security Misconfiguration**
   - Default credentials
   - Unnecessary features
   - Verbose error messages

6. **Vulnerable Components**
   - Outdated dependencies
   - Known CVEs

7. **Authentication Failures**
   - Weak passwords allowed
   - Missing MFA
   - Session fixation

8. **Data Integrity Failures**
   - Unsigned data
   - Deserialization issues

9. **Logging Failures**
   - Missing audit logs
   - Sensitive data in logs

10. **SSRF**
    - Unauthorized internal requests

Reference [vulnerability-patterns.md](references/vulnerability-patterns.md) for detection and prevention.

## Secure Coding by Language

See [secure-coding/python.md](references/secure-coding/python.md), [secure-coding/javascript.md](references/secure-coding/javascript.md), etc.

Quick reference:

**Python:**
- Use parameterized queries
- Avoid `eval()` and `exec()`
- Validate file paths
- Set `werkzeug debugger` off in prod

**JavaScript:**
- Avoid `innerHTML`
- Sanitize user input
- Use strict CSP headers
- Validate URLs before fetch

**SQL:**
- Never concatenate queries
- Use ORM or parameterized statements
- Least privilege DB users
- Input validation before DB

## Incident Response

### Security Incident Playbook

```markdown
## Detection
- Alert: Suspicious login pattern
- Source: SIEM / WAF logs

## Containment
1. Disable affected accounts
2. Revoke active sessions
3. Block suspicious IPs

## Investigation
1. Review access logs
2. Identify scope of access
3. Check for data exfiltration

## Recovery
1. Reset credentials
2. Patch vulnerability
3. Restore from clean backup if needed

## Post-Incident
1. Document timeline
2. Update detection rules
3. Improve controls
```

Use scripts/security-audit.py:
```bash
python scripts/security-audit.py \
  --source src/ \
  --dependencies requirements.txt \
  --output security-report.html
```

## Resources

- [vulnerability-patterns.md](references/vulnerability-patterns.md) - Common vulnerabilities
- [secure-coding/](references/secure-coding/) - Language-specific guides
- [threat-modeling.md](references/threat-modeling.md) - STRIDE methodology
