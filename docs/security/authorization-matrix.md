# CivicLens — Authorization Matrix

Status: v1.1 Hardened Specification
Related: security-audit.md, threat-model.md, authorization-model.md

## Resource Authorization Matrix

| Resource | Citizen | Agent | Scheme Admin | Admin | Enforcement Mechanism |
|---|---|---|---|---|---|
| **Own Profile** | R/W | Scoped (with active consent) | No | Restricted / Policy | Ownership check (`user_id == citizen_profile_id`) |
| **Own Documents** | R/W | Scoped (with active consent) | No | Restricted | Ownership check & signed S3 URL authorization |
| **Own Applications** | R/W | Scoped (with active consent) | No | Restricted | Ownership check & state machine permissions |
| **Citizen Records** | Own only | Consented citizens only | Restricted | Policy / Audit logged | Service layer consent check & active token filter |
| **Schemes Catalog** | R | Limited / Read | R/W (Drafts) | R/W | Role check (`scheme_admin` / `admin`) |
| **Eligibility Rules** | R | No | R/W (Drafts) | Policy | Four-eyes check (`author_id != reviewer_id`) |
| **Audit Logs** | No | No | Limited | R | Admin role assertion (`role == "admin"`) |
| **System Config** | No | No | No | R/W | System Admin role assertion (`role == "admin"`) |

*Legend: R = Read, W = Write, Scoped = Restricted to consented citizen profiles with active non-expired consent token.*
