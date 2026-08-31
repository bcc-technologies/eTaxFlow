# Inbound Security Controls Policy Review Lab

**Phase:** 034  
**Status:** LAB_ONLY — policy review, not production security approval  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Policy scope:** `NON_PRODUCTION_LAB_ONLY`  
**Policy decision:** `SECURITY_POLICY_BLOCKED`

## 1. Purpose

Lab-only policy review for inbound DGII-facing receiver security controls.

- No public endpoint activation
- No production security approval
- No DGII calls, no TrackId
- No certification claim

## 2. Scope

Control families reviewed:

- Endpoint disabled-by-default gate
- DNS/TLS verification gate
- Allowed HTTP methods
- Request body size cap
- Content-Type allowlist
- Safe XML parser policy
- External entity and network resolution disabled
- Public route no-parse / no-persist while disabled
- Rate limiting / IP throttling
- Authentication/authorization for future portal integration
- Logging redaction
- Raw XML storage policy
- Duplicate/replay detection
- Signature verification / trust-chain / revocation
- Audit/retention and incident response
- Secret management and environment separation
- Human approval gates (Phase 024)

## 3. Boundary warning

- Passing this lab review ≠ enable endpoints
- Passing this lab review ≠ DGII certification
- Passing this lab review ≠ legal/compliance approval
- This is **not** a production penetration test
- This is **not** a substitute for security owner review

## 4. Control vocabulary

| Status | Meaning |
|---|---|
| `CONTROL_PASS` | Control currently satisfied in lab/design |
| `CONTROL_FAIL` | Control violated |
| `CONTROL_WARNING` | Partial / placeholder / needs attention |
| `CONTROL_NOT_IMPLEMENTED` | Required control not built |
| `CONTROL_NOT_APPLICABLE` | Not applicable in current phase |
| `CONTROL_MANUAL_REVIEW_REQUIRED` | Human owner must review/sign off |

## 5. Policy decision vocabulary

| Decision | Meaning |
|---|---|
| `SECURITY_POLICY_BLOCKED` | Public processing must remain disabled |
| `SECURITY_POLICY_LAB_ONLY` | Lab evaluation only |
| `SECURITY_POLICY_MANUAL_REVIEW_REQUIRED` | Human gates incomplete |
| `SECURITY_POLICY_READY_FOR_HUMAN_REVIEW` | Catalog complete for human review (not production ready) |

**Not defined:** `READY_FOR_PRODUCTION`, `DGII_APPROVED`.

## 6. Required gates before any future public processing

1. `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS` cannot be true by default
2. DNS/TLS must be externally verified
3. Body size limit must be **enforced** (placeholder ≠ enforced)
4. Content-Type allowlist must be **enforced**
5. Safe parser must be enforced on any live parse path
6. Rate limiting must be implemented
7. Logging redaction must be implemented and approved
8. Production signature verification must be approved and implemented
9. Certificate trust-chain and revocation policy must be approved
10. Persistence policy must be approved
11. Audit and retention policy must be legally reviewed
12. Phase 024 human authorization gate must be signed off

## 7. Lab pipeline

1. Load settings and known lab/design evidence
2. Evaluate deterministic control catalog
3. Produce `SECURITY_POLICY_BLOCKED` report
4. Optionally export metadata-only JSON under `runtime/dgii_security_reports/`
5. No DB writes, no public route changes, no DGII, no TrackId

```bash
python manage.py dgii_inbound_security_policy_lab
python manage.py dgii_inbound_security_policy_lab --json
python manage.py dgii_inbound_security_policy_lab --summary-only
python manage.py dgii_inbound_security_policy_lab --export-report --json
```

## 8. Exit criteria

- [x] Security policy command works
- [x] JSON output parseable
- [x] Disabled endpoint guarantees tested
- [x] Report remains lab-only
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/inbound_security_policy_lab.py`
- `ecf/management/commands/dgii_inbound_security_policy_lab.py`
- `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md`

- `docs/dgii/lab/NON_PRODUCTION_INBOUND_REPORTING_EXPORT_LAB.md` (Phase 035)

- `docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md` (Phase 036)

- `docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md` (Phase 037)

- `docs/dgii/certification/FINAL_NON_PRODUCTION_PRE_CERT_GO_NO_GO_REVIEW.md` (Phase 038)

## Next phase

**Phase 039** — Final inbound lab audit report — still no public endpoints, no DGII live, no TrackId.
