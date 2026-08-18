# Checkpoint 029 — Local Inbound Schema Validation Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`aa50821` — Add non-production inbound XML lab

## Files changed

- `CHECKPOINT_029_LOCAL_INBOUND_SCHEMA_VALIDATION_START.md` (new)
- `CHECKPOINT_029_LOCAL_INBOUND_SCHEMA_VALIDATION_COMPLETE.md` (new)
- `docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md` (new)
- `ecf/dgii/inbound_schema_lab.py` (new)
- `ecf/dgii/inbound_schema_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_schema_lab.py` (new)
- `tests/test_dgii_inbound_schema_lab.py` (new)
- `ecf/dgii/inbound_lab.py` — schema_validation_* metadata (not run by default)
- `ecf/dgii/inbound_lab_readiness.py` — local-only XSD wording
- `ecf/dgii/receiver.py` — schema lab contract fields
- `ecf/management/commands/dgii_inbound_xml_lab.py`
- `ecf/management/commands/dgii_receiver_contract.py`
- `ecf/management/commands/dgii_readiness_report.py`
- `tests/test_dgii_readiness_report.py`
- `README.md`, `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md`, `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md`, `docs/dgii/PRE_CERTIFICATION_READINESS_CHECKLIST.md`

## Migrations

No changes detected.

## Schema lab documentation created

`docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md` — purpose, mapping, pipeline, result fields, synthetic-invalid expected, LOCAL_OFFLINE_ONLY boundary.

## XSD mapping summary

| Type | Local file | Status |
|---|---|---|
| ECF | `docs/dgii/sources/e-CF_31_v1.0.xsd` | Mapped (Tipo 31 lab only) |
| ARECF | `docs/dgii/sources/ARECF_v1.0.xsd` | Mapped |
| ACECF | `docs/dgii/sources/ACECF_v1.0.xsd` | Mapped |
| UNKNOWN | none | Unmapped |

Known source defect: `e-CF_31_v1.0.xsd` may fail to compile (`IndicadorServicioTodoIncluidoType` unresolved). The lab reports `xsd_compiled=false` instead of claiming a pass. Official XSDs were not modified.

## Local schema lab command summary

`python manage.py dgii_inbound_schema_lab`:

- Default path: `tests/fixtures/dgii/inbound_lab/`
- `--path`, `--json`, `--fail-on-invalid`, `--summary-only`
- Prints `NOT_DGII_COMPLIANT`, `LOCAL_OFFLINE_ONLY`, `NON_OFFICIAL_SYNTHETIC_SAMPLE`, `not_certification_evidence=true`
- No DB mutation, no TrackId, no DGII calls, no remote XSD fetch

`dgii_inbound_xml_lab` still classification-only: `schema_validation_status=NOT_RUN_BY_DEFAULT`.

## Expected validation behavior for synthetic fixtures

All 8 synthetic fixtures report `local_xsd_valid=false` (minimal XML and/or unmapped/invalid/XSD compile defect). Honest reporting, not forced validity. Placeholder Signature remains `signature_verified=false`.

## Receiver contract update summary

- `local_inbound_schema_lab_available`: true
- `schema_validation_scope`: LOCAL_OFFLINE_ONLY
- `schema_validation_command`: dgii_inbound_schema_lab
- `schema_validation_certification_evidence`: false
- `supported_schema_roots`: ECF, ARECF, ACECF
- `schema_validation`: NOT_CLAIMED (global claim still refused)
- `persistence` / `signature_verification`: NOT_IMPLEMENTED
- `public_endpoints_enabled`: false

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no schema lab invocation from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `dgii_call_made`: **false**
- `track_id`: **null**
- Blockers: **58** (8 new Phase 029 schema lab blockers)

## Final pytest result

**286 passed** (was 263 at Phase 029 start).

## Remaining blockers (Phase 029 additions)

- `local_inbound_schema_validation_lab_only`
- `local_xsd_validation_not_dgii_acceptance`
- `official_certification_fixtures_not_loaded`
- `inbound_xsd_errors_not_resolved`
- `inbound_schema_mapping_not_human_reviewed`
- `inbound_signature_validation_still_not_implemented`
- `inbound_public_processing_still_disabled`
- `inbound_persistence_still_not_implemented`

Plus all prior Phase 024–028 blockers.

## Exact next recommended phase

**Phase 030 — Local inbound signature verification lab** — still non-production, offline, no live DGII, no TrackId, no public endpoint enablement.
