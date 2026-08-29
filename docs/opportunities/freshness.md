# Freshness & Status Automation Policy

## Deadline Status Lifecycle
- `UPCOMING`: `application_open_date > NOW()`
- `OPEN`: `application_deadline > NOW()`
- `CLOSING_SOON`: `application_deadline <= NOW() + 5 days`
- `CLOSED`: `application_deadline <= NOW()`
- `DATE_UNKNOWN`: No deadline specified in official notice.

## Stale Data Handling
- Sources failing to complete successful crawl within 3x expected window marked `STALE`.
- Opportunities retain verified timestamps (`last_seen_at`, `last_verified_at`). Stale listings show verification age on citizen UI.
