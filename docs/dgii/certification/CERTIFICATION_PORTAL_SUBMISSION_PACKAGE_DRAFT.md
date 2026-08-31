# Certification Portal Submission Package Draft

**Phase:** 037  
**Status:** DRAFT_ONLY — not a portal submission  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Package scope:** `DRAFT_ONLY` · `PACKAGE_BLOCKED`

## 1. Purpose

Draft-only package for future DGII certification portal software postulation.

- No portal submission
- No XML submission
- No signing
- No DGII call / TrackId
- No certification claim

## 2. Scope

Draft package includes:

- Software postulation fields
- Planned endpoint URLs
- Endpoint plan / receiver contract summaries
- Staging evidence / security policy / inbound reporting summaries
- Readiness blocker summary
- Human decisions required
- Explicit no-submission warning

## 3. Boundary warning

- This package is **not** a portal submission
- This package is **not** a signed XML
- This package is **not** DGII acceptance or certification evidence
- Planned URLs are **not** externally verified unless manual evidence exists
- Public endpoints remain **DISABLED**
- DGII submission remains **forbidden**

## 4. Draft portal field vocabulary

| Status | Meaning |
|---|---|
| `PACKAGE_DRAFT_ONLY` | Lab draft artifact |
| `PACKAGE_BLOCKED` | Default; unresolved gates |
| `PACKAGE_MANUAL_REVIEW_REQUIRED` | Humans must review |
| `PACKAGE_READY_FOR_HUMAN_REVIEW` | Package assembled for human review only |

**Do not use:** `PACKAGE_READY_FOR_SUBMISSION`.

## 5. Draft software fields

Defaults:

- `software_type` = `PROPIO`
- `software_name` = `eTaxFlow`
- `software_version` from app setting
- `public_base_url` from `ETAXFLOW_PUBLIC_BASE_URL` or blank
- Planned URLs from base + `/fe/recepcion/api/ecf`, `/fe/aprobacioncomercial/api/ecf`, `/fe/autenticacion/api/semilla`, `/fe/autenticacion/api/validacioncertificado`
- Provider fields `NOT_APPLICABLE_FOR_SOFTWARE_PROPIO`
- `package_status` = `PACKAGE_BLOCKED`
- `submission_allowed` = false
- `requires_human_review` = true

## 6. Required unresolved gates

- Phase 024 authorization gate not signed off
- Public base URL not externally verified
- DNS/TLS evidence not approved
- Disabled endpoint evidence not approved
- Security / tax-compliance owner reviews not completed
- Production signing architecture not approved
- Production signature verification not implemented
- Certificate trust-chain and revocation policy not implemented
- Portal credentials not confirmed
- Human decision to proceed not granted

## 7. Lab pipeline

```bash
python manage.py dgii_certification_package_lab
python manage.py dgii_certification_package_lab --json
python manage.py dgii_certification_package_lab --summary-only
python manage.py dgii_certification_package_lab --export-package --json
```

## 8. Exit criteria

- [x] Command works; JSON parseable; package export works
- [x] Package remains draft-only; `submission_allowed=false`
- [x] Public routes remain disabled
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/certification_package_lab.py`
- `ecf/management/commands/dgii_certification_package_lab.py`

## Next phase

**Phase 038 — Final non-production pre-cert go/no-go review** — still no public endpoints, no DGII live, no TrackId.
