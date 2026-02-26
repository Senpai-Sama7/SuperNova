---
name: cloudflare-403-triage
description: Triage and remediate Cloudflare/WAF blocks that manifest as HTTP 403/503 with a "Just a moment..." HTML page or `__cf_chl`/challenge markers. Use when an app fails to load because a request is being blocked (browser or API client), including cases where code is incorrectly calling private web endpoints (e.g., `chatgpt.com/backend-api/...`) and must be changed to supported official APIs. Use to add defensive error handling that detects challenge pages and fails gracefully.
---

# Cloudflare 403 Triage

## Goal

Identify which request is being blocked, determine whether the fix is (a) changing your code/config, (b) fixing your own Cloudflare/WAF rules, or (c) a third-party block you cannot programmatically work around, then implement the compliant fix.

## Workflow

### 1) Capture the failing request precisely

Collect:
- Exact URL + method
- Status code
- A short body excerpt (first ~200 chars) and content-type
- Where it happens (browser UI, server-side job, mobile app, CI)

If you have a repo/workspace, run `scripts/scan_for_private_web_endpoints.sh` to find likely offenders.

### 2) Classify the block

1. **Private web endpoint / scraping** (common with `chatgpt.com/backend-api/...` and similar):
   - Fix is to stop using that endpoint and switch to a supported official API/SDK.
   - Do not attempt to bypass Cloudflare or bot protections.
2. **Your own domain behind Cloudflare**:
   - Fix is in Cloudflare (WAF/Bot Fight Mode/Firewall rules/rate limits) or your origin (headers, redirects, auth).
3. **Third-party domain you don't control**:
   - Fix is typically user-side (browser settings/network) or negotiating proper access with the service owner.

### 3) Apply the correct fix

#### A) If the request is to `chatgpt.com/backend-api/...`

Treat it as unsupported:
- Replace the integration with the official OpenAI API (or another provider's supported API).
- Update docs/config to avoid relying on ChatGPT web internals.
- Add explicit error messaging: "This endpoint is blocked/unsupported; configure an API key and use the supported integration."

#### B) If it is your domain behind Cloudflare

Do:
- Verify the request path is intended to be public.
- Check Cloudflare security events/logs for the block reason and rule ID.
- Adjust firewall/WAF/bot rules narrowly (route-based, ASN/country/IP range where appropriate).
- Ensure your app sends normal browser headers only if it is actually a browser; for server-to-server, use stable auth.

Do not:
- Add hacks to defeat challenges.

#### C) If it is a browser seeing "Just a moment..."

Do:
- Ensure JavaScript and cookies are enabled.
- Disable VPN/proxy and aggressive privacy extensions for that site.
- Clear site data (cookies/local storage) and re-auth.
- Try a different network.

### 4) Add defensive handling in code (when applicable)

If your app expects JSON but gets HTML challenge pages, detect and fail fast:
- Check `content-type` starts with `text/html`
- Search for known markers (see `references/signatures.md`)
- Surface a structured error with the blocked URL and remediation hint

## Resources

### scripts/
- `scripts/scan_for_private_web_endpoints.sh`: grep the workspace for common private web endpoints and Cloudflare-challenge markers.

### references/
- `references/signatures.md`: lightweight signatures to identify challenge pages in logs/responses.
