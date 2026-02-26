# Challenge Page Signatures

Use these as heuristics to detect "blocked by WAF/Cloudflare" responses when you expected JSON.

## Common HTML markers

- `<title>Just a moment...</title>`
- `window._cf_chl_opt`
- `/cdn-cgi/challenge-platform/`
- `__cf_chl_tk`
- `cf-ray`
- `<meta name="robots" content="noindex,nofollow">`
- Response `content-type: text/html` (or missing/incorrect content-type)

## Typical failure modes in apps

- Client expects JSON and crashes on HTML.
- UI shows a generic "Failed to load apps/connectors" while the real issue is the upstream is blocked.
- Server-side jobs get 403/503 and retry forever without surfacing "blocked by WAF".

## Guidance

- Prefer supported APIs instead of private web endpoints.
- If the domain is yours, fix in Cloudflare/WAF configuration and origin auth.
- If the domain is third-party, treat it as "access denied" and provide a user-actionable remediation message.
