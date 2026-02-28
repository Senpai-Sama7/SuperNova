# Security Policy

## Supported scope

This repository is under active development. Security fixes are accepted for the current `main` branch.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for suspected vulnerabilities.

Instead, report privately with:
- a clear description of the issue
- affected files, endpoints, or workflows
- reproduction steps or proof of concept
- potential impact
- any suggested mitigation

If you already exposed credentials, rotate them immediately before reporting.

## Immediate repository safety rules

The following files must never be committed to source control:
- `.env`
- `.env.local`
- `.env.production`
- any file containing live API keys, cloud credentials, JWT secrets, or database passwords
- generated tarballs, proof bundles, database dumps, or backup archives

Allowed tracked environment templates must be documentation-only:
- `.env.example`
- `.env.production.example`

## Security expectations for contributors

Before opening a pull request:
- run repository hygiene checks
- ensure only template environment files are tracked
- ensure no binary artifacts or backup archives are tracked
- ensure new configuration defaults are safe for development and explicit for production
- prefer GitHub Releases or artifact storage for distributable bundles instead of committing archives

## Operational guidance

If a secret is ever committed:
1. rotate it immediately
2. remove the tracked file in the next commit
3. inspect CI and deployment systems for reuse
4. document follow-up remediation in the pull request or incident record
