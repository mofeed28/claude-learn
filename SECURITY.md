# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in claude-learn, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer directly or use GitHub's private vulnerability reporting feature.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix release**: Within 2 weeks for critical issues

### Scope

The following are in scope:

- SSRF vulnerabilities in the scraper
- Path traversal in output file handling
- Code injection via user input
- Denial of service via resource exhaustion
- Cache poisoning

The following are out of scope:

- Issues in dependencies (report to the upstream project)
- Social engineering
- Issues requiring physical access

## Security Features

claude-learn includes the following security measures:

- **SSRF protection**: Blocks requests to private/loopback IP ranges
- **Path traversal protection**: Validates output paths against cwd/home
- **Input validation**: Validates URLs, timeouts, and configuration values
- **Rate limiting**: Per-domain request throttling with race condition protection
