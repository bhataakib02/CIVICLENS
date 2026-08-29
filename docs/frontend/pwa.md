# Progressive Web App (PWA)

Status: v1.0 draft
Related: frontend-architecture.md, product/non-functional-requirements.md (NFR-ACC-2)

## 1. Why PWA

The primary citizen device target is low-end Android (2GB RAM class) on
constrained networks (NFR-ACC-2). A PWA gives an installable,
app-like experience (home screen icon, offline shell) without the
distribution friction and update-latency of native app store releases —
important given how quickly scheme information can change and needs to
reach citizens.

## 2. Requirements

- Service worker caching an app shell so the UI loads (even if showing
  stale/cached data with a clear staleness indicator) on a poor or
  temporarily absent connection.
- Web App Manifest for installability (home screen icon, splash screen,
  standalone display mode).
- Aggressive asset budgeting: initial load JS/CSS payload targets are set
  and tracked in CI (bundle-size checks), since every kilobyte matters on
  2G/3G-equivalent conditions.
- Images served responsively (appropriately sized/compressed per device),
  never a desktop-weight asset served unconditionally to a constrained
  device.

## 3. What Works Offline vs. Requires Connectivity

| Works offline (cached) | Requires connectivity |
|---|---|
| Previously viewed scheme details | New scheme search/browse |
| Previously computed eligibility results (shown as stale) | New eligibility check, document upload, application submit |
| In-progress, locally-persisted application draft | Assistant chat (always requires live connection) |

The offline story is "don't lose the citizen's progress or leave them with
a blank screen," not "fully functional offline" — actions that require the
server are clearly gated with a connectivity-required indicator rather
than silently failing.

## 4. Update Delivery

Service worker update-on-reload strategy with a visible "new version
available, refresh to update" prompt — critical given scheme information
can change and a citizen shouldn't act on a stale cached version of
eligibility rules indefinitely.
