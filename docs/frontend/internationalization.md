# Internationalization (i18n)

Status: v1.0 draft
Related: product/non-functional-requirements.md (NFR-ACC-3), ai/prompt-engineering.md §4

## 1. Launch Languages

Hindi and English, with the i18n framework built to support adding
further regional languages without requiring redeployment (NFR-ACC-3) —
translation resources are data (loaded resource files / a translation
management system), not compiled into the app bundle language-by-language.

## 2. Scope of Translation

- All static UI copy (buttons, labels, error messages, help text).
- Scheme catalog content (`scheme_versions.benefits_summary`,
  `eligibility_rules.explanation_text`) — authored or translated per
  scheme, since this is domain content, not generic UI string.
- Assistant responses — generated directly in the citizen's selected
  language (ai/prompt-engineering.md §4), not machine-translated after
  the fact, since translation-after-generation risks losing citation
  fidelity.
- Document type names and form field labels used in the document upload
  and application flows.

## 3. Locale-Sensitive Formatting

Dates, currency (₹), and numbers formatted per locale convention; income
figures and thresholds always shown with the ₹ symbol and Indian
digit-grouping convention (e.g., ₹2,50,000, not ₹250,000) since this is
the convention citizens will recognize from government documents
themselves.

## 4. Content Ownership

UI string translations are owned by the frontend team's i18n resource
files; scheme-domain content translations are owned by scheme
administrators as part of scheme authoring (docs/product/functional-requirements.md
FR-ADMIN-1) — a scheme isn't considered fully published if its
citizen-facing explanation text is missing a launch-required language.
