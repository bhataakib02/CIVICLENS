# User Stories

Status: v1.0 draft
Related: user-personas.md, functional-requirements.md

Format: As a [persona], I want [capability], so that [outcome]. Each maps
to one or more `FR-*` IDs from functional-requirements.md.

## Citizen (Meera)

- As a citizen, I want to answer a few basic questions and immediately see
  schemes I might qualify for, so that I don't have to know scheme names
  in advance. (FR-SCHEME-1, FR-ELIGIBILITY-3)
- As a citizen, I want to see exactly why I passed or failed each
  eligibility condition, so that I can trust the result or know what
  would need to change. (FR-ELIGIBILITY-2)
- As a citizen, I want to upload my documents once and reuse them across
  applications, so that I don't repeat the same paperwork every time.
  (FR-DOCS-5)
- As a citizen, I want to ask a question in my own words and get an
  answer I can verify against the actual government document, so that I
  don't have to fully trust a chatbot blindly. (FR-ASSISTANT-1, FR-ASSISTANT-2)
- As a citizen, I want to know if my application status changes, so that
  I don't have to keep checking manually. (FR-NOTIFY-1)

## Agent (Ravi)

- As an agent, I want explicit citizen consent before I can act on their
  behalf, so that I have a clear, auditable basis for helping them.
  (FR-CONSENT-1)
- As an agent, I want to move quickly between citizens' profiles without
  data bleeding between them, so that I can serve many people accurately
  in a day. (FR-AUTH-4)

## Scheme Administrator (Dr. Sharma)

- As a scheme administrator, I want to author eligibility rules in a
  structured editor rather than writing code, so that I can update policy
  without engineering involvement. (FR-ADMIN-1)
- As a scheme administrator, I want to simulate a rule change against
  real (anonymized) profiles before publishing, so that I understand its
  impact before it affects citizens. (FR-ELIGIBILITY-5)
- As a scheme administrator, I want a second reviewer required before my
  changes go live, so that mistakes are caught before affecting citizens.
  (FR-ADMIN-2)

## Ops/Support (Priya)

- As an ops team member, I want to be alerted when a knowledge source
  goes stale, so that CivicLens never serves outdated policy information
  silently. (FR-ADMIN-3)
- As an ops team member, I want to filter audit logs by user and action,
  so that I can investigate a reported issue efficiently. (FR-ADMIN-4)
