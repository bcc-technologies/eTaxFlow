# Checkpoint 032 — Non-production Inbound Workflow Routing Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`f7adeea` — Add non-production inbound persistence lab

## Files changed

- `CHECKPOINT_032_NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB_START.md` (new)
- `CHECKPOINT_032_NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB_COMPLETE.md` (new)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB.md` (new)
- `ecf/dgii/inbound_workflow_lab.py` (new)
- `ecf/dgii/inbound_workflow_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_workflow_lab.py` (new)
- `ecf/migrations/0005_inbound_xml_lab_workflow_event.py` (new)
- `tests/test_dgii_inbound_workflow_lab.py` (new)
- Updates: `ecf/models.py`, `ecf/admin.py`, inbound XML/schema/signature/persistence labs, receiver contract, readiness report, README and related docs

## Migrations created

`ecf/migrations/0005_inbound_xml_lab_workflow_event.py` — Create model `InboundXMLLabWorkflowEvent`

## Workflow lab documentation created

`docs/dgii/lab/NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB.md`

## Model summary

`ecf.InboundXMLLabWorkflowEvent` — FK to `InboundXMLLabRecord` only; no Invoice/Document/ECFDocument links.

- Forced defaults: `compliance_status=NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, `certification_evidence=false`, `track_id=null`, `dgii_call_made=false`, `lab_mode=NON_PRODUCTION_LAB_ONLY`
- Admin is read-only (no add/change/delete, no submit/TrackId actions)

## Workflow command summary

`python manage.py dgii_inbound_workflow_lab`

- `--path` file or directory
- `--from-lab-records`
- `--record-id ID`
- `--json`
- `--apply-lab-workflow`
- `--summary-only`
- `--limit N`

Service: `ecf/dgii/inbound_workflow_lab.py` (`decide_lab_workflow_route`, `route_lab_record`, `route_path_via_persistence_lab`).

## Dry-run behavior

Default mode is **DRY_RUN**. Computes routes; **no** `InboundXMLLabWorkflowEvent` write.

Verified: `result_count=8`, `applied_count=0`, `apply_lab_workflow=false`.

## Explicit apply behavior

`--apply-lab-workflow` writes **only** `InboundXMLLabWorkflowEvent` rows. With `--path`, may upsert `InboundXMLLabRecord` via existing persistence service first. No Invoice/Document/ECFDocument/TrackId.

## Routing rule summary (priority)

1. Invalid XML → `LAB_ROUTE_INVALID_XML_REVIEW`
2. Unsupported root → `LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW`
3. Duplicate SHA-256 re-ingest → `LAB_ROUTE_DUPLICATE_REVIEW`
4. Schema compile/validation issue → `LAB_ROUTE_SCHEMA_ISSUE_REVIEW`
5. Signature missing/unverified → `LAB_ROUTE_SIGNATURE_ISSUE_REVIEW`
6. ECF / ARECF / ACECF → document-specific review routes
7. Fallback → `LAB_ROUTE_MANUAL_REVIEW`

Synthetic fixture dry-run routes (8 fixtures): 6 schema issue, 1 invalid XML, 1 unsupported root.

## Private key safety check result

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` matched only pre-existing `.conda/.../api-ms-win-crt-private-l1-1-0.dll` (Windows CRT DLL name). **False positive.** No private key files added.

## Receiver contract update summary

- `non_production_inbound_workflow_lab_available`: true
- `workflow_scope`: NON_PRODUCTION_LAB_ONLY
- `workflow_command`: dgii_inbound_workflow_lab
- `production_workflow_ready`: false
- `public_route_workflow_enabled`: false
- `fiscal_acceptance_workflow_enabled`: false
- `track_id_creation`: DISABLED
- `certification_evidence`: false

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no workflow lab import/call, no DB write from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `production_signature_ready`: **false**
- `dgii_call_made`: **false**
- `track_id`: **null**
- `not_certification_evidence`: **true**
- Blockers: **81** (8 new Phase 032 workflow lab blockers)

## Final pytest result

**352 passed** (was 328 at Phase 032 start).

## Remaining blockers (Phase 032 additions)

- `inbound_workflow_lab_only`
- `production_inbound_workflow_not_implemented`
- `public_route_workflow_disabled`
- `fiscal_acceptance_workflow_not_implemented`
- `acuse_generation_not_implemented`
- `aprobacion_comercial_generation_not_implemented`
- `workflow_policy_not_approved`
- `inbound_workflow_not_certification_evidence`

Plus prior Phase 024–031 blockers.

## Exact next recommended phase

**Phase 033 — Non-production inbound audit and retention policy lab** — audit/retention/export/cleanup policy for lab records; still no public endpoints, no DGII live, no TrackId.
