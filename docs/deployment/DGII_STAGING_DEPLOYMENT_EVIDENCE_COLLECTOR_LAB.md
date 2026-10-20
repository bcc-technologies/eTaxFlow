# DGII Staging Deployment Evidence Collector Lab

**Phase:** 036  
**Status:** LAB_ONLY — offline/manual evidence collection, not deployment  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Evidence scope:** `NON_PRODUCTION_LAB_ONLY`

## 1. Purpose

Offline/manual staging evidence collection for future DGII-facing receiver deployment review.

- No deployment
- No live network checks (DNS, TLS, HTTPS, HTTP)
- No public endpoint activation
- No DGII calls, no TrackId
- No certification claim
- No staging approval claim

## 2. Scope

Manual evidence categories:

- DNS configured
- TLS certificate present
- HTTPS reachable (manual/external only)
- Public base URL configured
- Disabled endpoints externally verified
- Disabled POST externally verified
- No XML parse / no DB write externally verified
- Environment variables reviewed
- Staging DB separated
- Secrets / logging / rate-limit policy reviewed
- Security owner review
- Tax/compliance owner review
- Phase 024 authorization gate status

## 3. Boundary warning

- Evidence **template** ≠ evidence
- Manual/uploaded evidence ≠ DGII certification
- Staging evidence ≠ production approval
- External verification is **manual** in this phase
- This command **must not** perform network checks
- Public `/fe/...` routes remain **503 DISABLED**

## 4. Evidence status vocabulary

| Status | Meaning |
|---|---|
| `EVIDENCE_MISSING` | No evidence supplied |
| `EVIDENCE_PROVIDED` | Payload/reference present (still requires human review) |
| `EVIDENCE_INCOMPLETE` | Partial fields only |
| `EVIDENCE_NOT_VERIFIED` | Present but not verified offline/manual |
| `EVIDENCE_MANUAL_REVIEW_REQUIRED` | Human review outstanding |
| `EVIDENCE_REJECTED` | Reviewer rejected |

## 5. Staging decision vocabulary

| Decision | Meaning |
|---|---|
| `STAGING_EVIDENCE_BLOCKED` | Default; insufficient for human review package |
| `STAGING_EVIDENCE_LAB_ONLY` | Lab/template activity only |
| `STAGING_EVIDENCE_MANUAL_REVIEW_REQUIRED` | Package exists; humans must review |
| `STAGING_EVIDENCE_READY_FOR_HUMAN_REVIEW` | All required items PROVIDED + manual review flags set (still not approved) |

**Do not use:** `STAGING_READY_FOR_DGII`, `STAGING_APPROVED`.

## 6. Evidence file format

JSON items include:

- `evidence_id`, `category`, `status`
- `provided_by`, `reviewed_by`, `reviewed_at`
- `source_reference`, `notes`, `evidence_hash`
- `manual_review_required`
- `certification_evidence` (always false)
- `dgii_submission_allowed` (always false)
- `track_id` (always null)
- `dgii_call_made` (always false)

## 7. Required evidence before any future portal submission

- DNS/TLS external verification
- Disabled endpoint screenshots or logs
- POST disabled verification
- Public base URL configuration evidence
- Staging DB separation evidence
- Secret policy evidence
- Logging redaction evidence
- Security owner review
- Tax/compliance owner review
- Phase 024 gate sign-off

## 8. Lab pipeline

```bash
python manage.py dgii_staging_evidence_lab
python manage.py dgii_staging_evidence_lab --json
python manage.py dgii_staging_evidence_lab --summary-only
python manage.py dgii_staging_evidence_lab --write-template --json
python manage.py dgii_staging_evidence_lab --export-report --json
python manage.py dgii_staging_evidence_lab --evidence-file runtime/dgii_staging_evidence/staging_evidence_template.json --json
```

## 9. Exit criteria

- [x] Template / validation / export commands work
- [x] JSON parseable; report lab-only
- [x] No network calls
- [x] Public routes remain disabled
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/staging_evidence_lab.py`
- `ecf/management/commands/dgii_staging_evidence_lab.py`
- `docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md` (Phase 026)

- `docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md` (Phase 037)

- `docs/dgii/certification/FINAL_NON_PRODUCTION_PRE_CERT_GO_NO_GO_REVIEW.md` (Phase 038)

## Next phase

**Phase 039** — Final inbound lab audit report — still no public endpoints, no DGII live, no TrackId.
