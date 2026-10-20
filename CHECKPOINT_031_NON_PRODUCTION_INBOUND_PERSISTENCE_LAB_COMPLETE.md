# Checkpoint 031 — Non-production Inbound Persistence Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`4a47093` — Add local inbound signature verification lab

## Files changed

- `CHECKPOINT_031_NON_PRODUCTION_INBOUND_PERSISTENCE_LAB_START.md` (new)
- `CHECKPOINT_031_NON_PRODUCTION_INBOUND_PERSISTENCE_LAB_COMPLETE.md` (new)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md` (new)
- `ecf/dgii/inbound_persistence_lab.py` (new)
- `ecf/dgii/inbound_persistence_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_persistence_lab.py` (new)
- `ecf/migrations/0004_inbound_xml_lab_record.py` (new)
- `tests/test_dgii_inbound_persistence_lab.py` (new)
- Updates: `ecf/models.py`, `ecf/admin.py`, inbound XML/schema/signature labs, receiver contract, readiness report, README and related docs

## Migrations created

`ecf/migrations/0004_inbound_xml_lab_record.py` — Create model `InboundXMLLabRecord`

## Persistence lab documentation created

`docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md`

## Model summary

`ecf.InboundXMLLabRecord` is a lab-only table with **no FK** to Invoice, Document, or ECFDocument.

- Unique indexed `raw_sha256`
- Forced defaults: `compliance_status=NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, `certification_evidence=false`, `track_id=null`, `dgii_call_made=false`, `lab_mode=NON_PRODUCTION_LAB_ONLY`, `signature_verified=false`, `production_signature_ready=false`
- Optional `raw_xml_text` (empty by default); `persisted_raw_xml=false` unless explicitly stored
- Admin is read-only (no add/change/delete, no submit/TrackId actions)

## Persistence command summary

`python manage.py dgii_inbound_persistence_lab`

- `--path` file or directory (default `tests/fixtures/dgii/inbound_lab/`)
- `--json`
- `--persist-lab-records`
- `--store-raw-lab-xml`
- `--allow-duplicates` (accepted; unique `raw_sha256` still upserts)
- `--summary-only`

Service: `ecf/dgii/inbound_persistence_lab.py` (`build_lab_record_payload`, `persist_lab_record`, `persist_path`).

## Dry-run behavior

Default mode is **DRY_RUN**. Analyze/classify/schema/signature summaries are printed; **no DB write**.

Verified: `result_count=8`, `created_count=0`, `persist_lab_records=false`.

## Explicit persist behavior

`--persist-lab-records` writes **only** `InboundXMLLabRecord` rows (`update_or_create` by `raw_sha256`). No Invoice / Document / ECFDocument / TrackId.

Verified: `created_count=8`, `track_id=null`, `persisted_raw_xml=false`, `compliance_status=NOT_DGII_COMPLIANT`.

## Raw XML storage behavior

Disabled by default. `--store-raw-lab-xml` stores UTF-8 text with replacement decode and sets `persisted_raw_xml=true`. Public routes never persist.

## Private key safety check result

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` matched only pre-existing `.conda/.../api-ms-win-crt-private-l1-1-0.dll` (Windows CRT DLL name). **False positive.** No `.pem`/`.p12`/`.pfx`/`.key` private key files added in this phase.

## Receiver contract update summary

- `non_production_inbound_persistence_lab_available`: true
- `persistence_scope`: NON_PRODUCTION_LAB_ONLY
- `persistence_command`: dgii_inbound_persistence_lab
- `production_persistence_ready`: false
- `public_route_persistence_enabled`: false
- `raw_xml_storage_default`: DISABLED
- `track_id_creation`: DISABLED
- `certification_evidence`: false
- Production `persistence`: **NOT_IMPLEMENTED** (unchanged)

XML/schema/signature labs report `persistence_status=NOT_RUN_BY_DEFAULT` and do not write DB.

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no persistence lab import/call, no DB write from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `production_signature_ready`: **false**
- `dgii_call_made`: **false**
- `track_id`: **null**
- `not_certification_evidence`: **true**
- Blockers: **73** (8 new Phase 031 persistence lab blockers)

## Final pytest result

**328 passed** (was 309 at Phase 031 start).

## Remaining blockers (Phase 031 additions)

- `inbound_persistence_lab_only`
- `production_inbound_persistence_not_implemented`
- `public_route_persistence_disabled`
- `raw_xml_storage_policy_not_approved`
- `inbound_lab_records_not_fiscal_documents`
- `inbound_persistence_not_certification_evidence`
- `inbound_business_workflow_not_implemented`
- `inbound_audit_policy_not_approved`

Plus prior Phase 024–030 blockers (including `inbound_persistence_still_not_implemented` and cryptographic XMLDSig `NOT_IMPLEMENTED`).

## Exact next recommended phase

**Phase 032 — Non-production inbound workflow routing lab** — still no public endpoints, no DGII live, no TrackId, no production signing.
