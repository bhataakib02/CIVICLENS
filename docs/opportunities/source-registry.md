# Source Registry & Trust Model

## Authority Levels
1. **OFFICIAL**: Government portals (`.gov.in`, `.nic.in`), Central/State ministries, Public Commissions (UPSC, SSC).
2. **VERIFIED_PARTNER**: Recognized public institutions and authorized statutory platforms.
3. **KNOWN_PRIVATE**: Verified corporate career portals (e.g. TCS, Infosys).
4. **UNVERIFIED**: Third-party aggregators (never surfaced as official government notices).

## Source Registry Schema
Every registered source tracks:
- `id`: UUID primary key
- `name`: Human readable title
- `domain`: Registered hostname
- `base_url`: Target entry URL
- `source_type`: `CENTRAL_GOVERNMENT`, `STATE_GOVERNMENT`, `PUBLIC_INSTITUTION`, `UNIVERSITY`, `PSU`, `PRIVATE_COMPANY`, `NGO`, `FOUNDATION`, `EDUCATIONAL_INSTITUTION`, `OTHER`
- `authority_level`: `OFFICIAL`, `VERIFIED_PARTNER`, `KNOWN_PRIVATE`, `UNVERIFIED`
- `crawl_frequency`: `30_minutes`, `hourly`, `3_hours`, `daily`
- `enabled`: Boolean active status flag
- `last_crawled_at`, `last_successful_crawl_at`, `last_error_at`, `last_error`
