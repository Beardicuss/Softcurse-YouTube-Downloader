# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Active  |
| < 1.0   | ❌ EOL     |

## Reporting a Vulnerability

> **⚠️ Do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability, please report it privately:

**Email:** softcurse@proton.me

Include the following in your report:

- Description of the vulnerability
- Steps to reproduce
- Impact assessment (what an attacker could do)
- Proof-of-concept code or screenshots (if applicable)

## Response Timeline

| Stage | Timeframe |
|-------|-----------|
| Acknowledgement | Within 48 hours |
| Initial assessment | Within 7 days |
| Patch or mitigation | Within 90 days of confirmation |
| Public disclosure | Coordinated after patch release |

## Security Advisories

Security advisories are published via [GitHub Security Advisories](https://github.com/Beardicuss/Softcurse-YouTube-Downloader/security/advisories).

## Out of Scope

The following are **not** considered vulnerabilities:

- Social engineering attacks against maintainers or users
- Denial of service on local desktop installations
- Issues in end-of-life versions
- Bugs in third-party dependencies (report upstream instead)
- Issues requiring physical access to the user's machine

## Bug Bounty

There is currently **no bug bounty program**. We appreciate responsible disclosure
and will credit reporters in the release notes (unless anonymity is requested).

## Security Best Practices for Contributors

- Never commit secrets, API keys, or credentials to the repository
- Pin dependency versions in `requirements.txt`
- Do not introduce network calls without documenting them
- Sanitize all user input (URLs, file paths, filenames)
- Use `subprocess` with explicit argument lists, never shell=True
