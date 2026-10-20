# Checkpoint 033 — Non-production Inbound Audit & Retention Policy Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`43f440e` — Add non-production inbound workflow routing lab  
(Phase 032 published: tag `dgii-phase-032-inbound-workflow-routing-lab`, PR #1 commented)

## Files changed

- `CHECKPOINT_033_NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB_START.md` (new)
- `CHECKPOINT_033_NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB_COMPLETE.md` (new)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB.md` (new)
- `ecf/dgii/inbound_audit_retention_lab.py` (new)
- `ecf/dgii/inbound_audit_retention_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_audit_retention_lab.py` (new)
- `ecf/migrations/0006_inbound_xml_lab_audit_event.py` (new)
- `tests/test_dgii_inbound_audit_retention_lab.py` (new)
- `runtime/dgii_lab_exports/.gitkeep` (new; export contents gitignored)
- Updates: models, admin, receiver contract, readiness, inbound labs, README, related docs, `.gitignore`

## Migrations created

`ecf/migrations/0006_inbound_xml_lab_audit_event.py` — Create model `InboundXMLLabAuditEvent`

## Audit retention lab documentation created

`docs/dgii/lab/NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB.md`

## Model summary

`ecf.InboundXMLLabAuditEvent` — optional FKs to `InboundXMLLabRecord` and `InboundXMLLabWorkflowEvent` only; no Invoice/Document/ECFDocument links.

- Forced defaults: `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, `certification_evidence=false`, `track_id=null`, `dgii_call_made=false`, `lab_mode=NON_PRODUCTION_LAB_ONLY`
- Admin read-only; no submit/approve/delete/purge/TrackId actions

## Audit retention command summary

`python manage.py dgii_inbound_audit_retention_lab`

- `--from-lab-records` / `--record-id` / `--limit` / `--retention-days` (default 30)
- `--json` / `--summary-only`
- `--apply-lab-audit` — write audit events only
- `--export-manifest` / `--export-path` — metadata-only under `runtime/dgii_lab_exports/` (path traversal rejected)

## Dry-run behavior

Default **DRY_RUN**: computes retention decisions; **no** `InboundXMLLabAuditEvent` write. Verified `result_count=8`, `applied_count=0`.

## Explicit apply behavior

`--apply-lab-audit` writes **only** `InboundXMLLabAuditEvent` rows. No Invoice/Document/ECFDocument/TrackId. Verified `applied_count=8`.

## Export manifest behavior

`--export-manifest` writes metadata-only JSON under `runtime/dgii_lab_exports/`. Does **not** include `raw_xml_text`. Unsafe paths outside the export root are rejected.

## No destructive deletion confirmation

Phase 033 has **no delete/purge implementation**. `destructive_retention_actions_enabled=false`. Purge candidates are decision labels only.

## Retention rule summary (priority)

1. certification_evidence / dgii_submission_allowed / track_id / dgii_call_made → `LAB_AUDIT_MANUAL_REVIEW_REQUIRED`
2. `persisted_raw_xml=true` → `LAB_RETENTION_RAW_XML_REVIEW`
3. age > retention_days → `LAB_RETENTION_PURGE_CANDIDATE`
4. else → `LAB_RETENTION_KEEP`

## Private key safety check result

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` matched only pre-existing `.conda/.../api-ms-win-crt-private-l1-1-0.dll` (Windows CRT DLL). **False positive.** No private key files added.

## Receiver contract update summary

- `non_production_inbound_audit_retention_lab_available`: true
- `audit_retention_scope`: NON_PRODUCTION_LAB_ONLY
- `audit_retention_command`: dgii_inbound_audit_retention_lab
- `production_audit_ready`: false
- `production_retention_ready`: false
- `public_route_audit_enabled`: false
- `destructive_retention_actions_enabled`: false
- `export_manifest_scope`: METADATA_ONLY

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no audit lab import/call, no DB write from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- Blockers: **89** (8 new Phase 033 blockers)

## Final pytest result

**374 passed** (was 352 at Phase 033 start).

## Remaining blockers (Phase 033 additions)

- `inbound_audit_retention_lab_only`
- `production_audit_trail_not_implemented`
- `production_retention_policy_not_approved`
- `public_route_audit_disabled`
- `destructive_retention_actions_disabled`
- `metadata_export_not_certification_evidence`
- `raw_xml_retention_policy_not_approved`
- `audit_retention_policy_not_legal_reviewed`

Plus prior Phase 024–032 blockers.

## Exact next recommended phase

**Phase 034 — Non-production inbound security controls / policy review lab** (body size, content-type, rate-limit design, still no public endpoints, no DGII live, no TrackId).
