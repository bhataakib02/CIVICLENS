# Deduplication & Versioning Engine

## Deterministic Matching
- `compute_content_hash`: SHA-256 hash of normalized `(organization, title, deadline)`.
- Secondary match via `source_identifier` and normalized regex title matching.

## Canonical Selection
- When identical opportunities appear on multiple sources, the canonical listing is assigned to the source with highest authority (`OFFICIAL` > `VERIFIED_PARTNER` > `KNOWN_PRIVATE` > `UNVERIFIED`).

## Version History
- Every change in deadline, application URL, eligibility, or description creates an immutable `OpportunityVersion` diff record and logs a structured `OpportunityChange`.
