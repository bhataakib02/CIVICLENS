# API Pagination

Status: v1.0 draft
Related: api-overview.md, openapi.yaml (SchemePage, ApplicationPage)

## 1. Convention

All list endpoints accept `page` (1-indexed, default 1) and `page_size`
(default 20, max 100) query parameters and return:

```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 137
}
```

## 2. Why Offset Pagination (not cursor-based) for v1.0

Scheme and application lists are bounded in practice (hundreds, not
millions, per citizen or per catalog at launch scale), and offset
pagination is simpler for the admin UI's "jump to page N" needs. Cursor-
based pagination is a candidate if `knowledge_chunks` or `audit_logs`
browsing ever needs it at larger scale — those are the two tables most
likely to outgrow offset pagination's performance characteristics.

## 3. Out-of-Range Requests

A `page` beyond the available range returns an empty `items` array with
the correct `total`, not an error — simplifies client-side "load more"
logic.

## 4. Consistency

Pagination is not guaranteed strictly consistent across concurrent writes
(no snapshot isolation across pages) — acceptable for this system's usage
patterns; a citizen re-browsing a list mid-update might see a scheme
shift pages, which has negligible practical impact.
