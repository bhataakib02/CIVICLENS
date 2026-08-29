# Use Cases

Status: v1.0 draft
Related: user-stories.md, functional-requirements.md

## UC-1: Discover Eligible Schemes

**Actor**: Citizen. **Preconditions**: Registered account.
**Flow**: Citizen provides initial profile fields → system runs bulk
eligibility check (FR-ELIGIBILITY-3) → ranked list returned, each entry
showing result category and benefit summary → citizen selects a scheme
for detail. **Postcondition**: `eligibility_checks` rows created/cached
per scheme evaluated.

## UC-2: Understand an Eligibility Result

**Actor**: Citizen. **Preconditions**: A prior eligibility check exists
for a scheme. **Flow**: Citizen opens scheme detail → sees rule-by-rule
breakdown (pass/fail/unknown) with plain-language explanation and source
citation per rule (FR-ELIGIBILITY-2). **Alternate flow**: Result is
`insufficient_data` → UI highlights which profile fields are missing and
prompts the citizen to fill them (FR-PROFILE-2).

## UC-3: Upload and Reuse a Document

**Actor**: Citizen. **Flow**: Citizen uploads a document → async OCR/
extraction (FR-DOCS-2) → citizen reviews and confirms extracted fields
(FR-DOCS-3) → document becomes available for attachment to any future
application requiring that document type (FR-DOCS-5). **Exception flow**:
Extraction confidence below threshold → citizen prompted to re-capture
(FR-DOCS-4).

## UC-4: Apply for a Scheme

**Actor**: Citizen. **Preconditions**: `eligible` or `likely_eligible`
result for the scheme. **Flow**: Citizen starts an application
(FR-APPLICATION-1) → attaches required verified documents + answers
scheme-specific questions → system validates completeness → citizen
submits → status transitions to `submitted`, notification sent
(FR-APPLICATION-2, FR-NOTIFY-1). **Alternate flow**: No direct portal
integration exists → citizen exports a completed application package as
PDF for manual submission (FR-APPLICATION-4).

## UC-5: Ask the Assistant a Question

**Actor**: Citizen. **Flow**: Citizen asks a free-text question →
assistant classifies intent → if eligibility-shaped, invokes the
deterministic engine as a tool; otherwise retrieves and generates a
cited answer (FR-ASSISTANT-1–4). **Exception flow**: No supporting source
found → assistant explicitly declines and offers human/agent handoff
(FR-ASSISTANT-3).

## UC-6: Author and Publish a Scheme Version

**Actor**: Scheme Administrator. **Flow**: Admin creates a draft
`scheme_version` referencing a knowledge source, authors eligibility
rules via the structured DSL editor (FR-ADMIN-1) → optionally runs a
simulation against anonymized profiles (FR-ELIGIBILITY-5) → submits for
review → a second scheme_admin approves → version publishes and becomes
effective (FR-ADMIN-2).

## UC-7: Agent Assists a Citizen

**Actor**: Agent, Citizen. **Preconditions**: Citizen has granted
`agent_assist` consent (FR-CONSENT-1). **Flow**: Agent authenticates
under their own account, selects the consented citizen, performs any
citizen-equivalent action (UC-1 through UC-5) on the citizen's behalf,
every action attributed to the agent account (FR-AUTH-4).
