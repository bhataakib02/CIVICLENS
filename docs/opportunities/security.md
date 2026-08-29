# Crawler Infrastructure Security Architecture

## SSRF Isolation
- All HTTP requests processed through `SafeFetcher`.
- Prohibits fetching internal network ranges:
  - `127.0.0.1`, `localhost`
  - `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
  - `169.254.169.254` (cloud metadata service)

## Sanitization & Prompt Injection
- External raw page text sanitized before LLM processing (`sanitize_external_text`).
- HTML scripts, tags, and adversarial instruction overrides (`ignore previous instructions`, `system prompt`) filtered.

## Open Redirect Protection
- Redirect targets validated against target domain rules before presenting Apply links to citizens.
