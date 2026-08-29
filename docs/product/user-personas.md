# User Personas

Status: v1.0 draft
Related: product-requirements.md §4, user-stories.md

## Meera — Citizen Applicant

Age 34, works as an agricultural laborer in rural Bihar, completed
schooling through class 8, owns a basic Android phone with intermittent
connectivity. Meera has heard about "government schemes" from neighbors
but has never successfully navigated a portal to check what she qualifies
for. She needs: plain-language explanations in Hindi, a process that works
on a slow connection, and confidence that what she's told is actually
correct before she spends a day traveling to submit paperwork.

## Ravi — Assisting Agent (CSC Operator)

Age 28, runs a Common Service Centre, helps 15-30 citizens a day with
government service applications for a small fee. Ravi needs speed (can't
spend 20 minutes per citizen), needs to handle multiple citizens'
profiles without them interfering with each other, and needs the tool to
be trustworthy enough that he can vouch for its answers to the people he
serves — his reputation depends on giving correct information.

## Dr. Anjali Sharma — Scheme Administrator

Works in a state welfare department, responsible for keeping her
department's schemes' eligibility criteria current in CivicLens. Not a
programmer — needs a structured authoring UI (ai/rule-dsl.md's admin
editor), not raw JSON. Accountable for accuracy: a wrongly-configured rule
either wrongly excludes eligible citizens or wrongly includes ineligible
ones, both bad, so the four-eyes review requirement (FR-ADMIN-2) matters
directly to her.

## Priya — CivicLens Ops/Support

Internal team member monitoring system health, knowledge base freshness,
and escalated citizen support cases. Needs the admin console's audit logs,
knowledge base staleness monitor, and case notes system
(FR-ADMIN-3/4, FR-CASEWORK-1) to do her job without needing to query the
database directly.
