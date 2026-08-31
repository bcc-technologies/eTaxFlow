# Non-Production Inbound Reporting Export Lab

**Phase:** 035  
**Status:** LAB_ONLY — metadata-only reporting, not a production dashboard  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Report scope:** `NON_PRODUCTION_LAB_ONLY`

## 1. Purpose

Metadata-only reporting for non-production inbound DGII labs.

- No public endpoint activation
- No production dashboard
- No DGII calls, no TrackId
- No certification claim
- **No raw XML** in exports by default

## 2. Scope

Consolidated summaries of:

- XML lab
- Schema lab
- Signature lab
- Persistence lab
- Workflow routing lab
- Audit/retention lab
- Security policy lab
- Endpoint plan
- Receiver contract
- Readiness blockers

## 3. Boundary warning

- Report ≠ DGII certification
- Report ≠ fiscal evidence
- Report ≠ production audit trail
- Report does **not** include raw XML by default
- Report does **not** enable public routes
- All outputs are `NON_PRODUCTION_LAB_ONLY`

## 4. Export formats

| Format | File |
|---|---|
| JSON | `inbound_lab_report.json` |
| CSV | `inbound_lab_summary.csv` |
| Markdown | `inbound_lab_summary.md` |
| Manifest | `manifest.json` |
| Bundle | directory under `runtime/dgii_lab_reports/` |

## 5. Required report fields

- `generated_at`, `report_scope`
- `compliance_status`, `dgii_submission_allowed`, `certification_evidence`
- `public_endpoints_enabled`, `track_id`, `dgii_call_made`
- `record_count`, `workflow_event_count`, `audit_event_count`
- `document_type_breakdown`, `schema_status_breakdown`, `signature_status_breakdown`
- `workflow_route_breakdown`, `retention_decision_breakdown`
- `security_control_summary`, `readiness_summary`
- `blocker_count`, `blockers`, `files_exported`

## 6. Lab pipeline

```bash
python manage.py dgii_inbound_reporting_lab
python manage.py dgii_inbound_reporting_lab --json
python manage.py dgii_inbound_reporting_lab --summary-only
python manage.py dgii_inbound_reporting_lab --export-bundle --json
```

## 7. Exit criteria

- [x] Command works; JSON parseable
- [x] CSV / Markdown / bundle export works
- [x] No raw XML exported
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/inbound_reporting_lab.py`
- `ecf/management/commands/dgii_inbound_reporting_lab.py`

- `docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md` (Phase 036)

- `docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md` (Phase 037)

## Next phase

**Phase 038** — Final non-production pre-cert go/no-go review — still no public endpoints, no DGII live, no TrackId.
