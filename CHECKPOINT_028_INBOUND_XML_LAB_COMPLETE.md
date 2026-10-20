# Checkpoint 028 — Inbound XML Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`c0e19bf` — Add pre-certification receiver endpoint contract

## Files changed

- `CHECKPOINT_028_INBOUND_XML_LAB_START.md` (new)
- `CHECKPOINT_028_INBOUND_XML_LAB_COMPLETE.md` (new)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md` (new)
- `tests/fixtures/dgii/inbound_lab/*.xml` (8 synthetic fixtures)
- `ecf/dgii/inbound_lab.py` (new)
- `ecf/dgii/inbound_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_xml_lab.py` (new)
- `ecf/dgii/receiver.py` (receiver contract metadata extended)
- `ecf/management/commands/dgii_readiness_report.py` (Phase 028 blockers)
- `ecf/management/commands/dgii_receiver_contract.py` (lab fields in output)
- `tests/test_dgii_inbound_xml_lab.py` (new)
- `tests/test_dgii_readiness_report.py` (updated)
- `README.md`, docs updates

## Migrations

No changes detected.

## Lab documentation created

`docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md` — purpose, scope, synthetic warning, pipeline, result fields, security, exit criteria.

## Synthetic fixtures summary

8 fixtures in `tests/fixtures/dgii/inbound_lab/`:

- ECF unsigned / signed placeholder
- ARECF unsigned / signed placeholder
- ACECF unsigned / signed placeholder
- Unknown root (`UNKNOWNLABROOT`)
- Invalid XML

All marked `NON_OFFICIAL_SYNTHETIC_SAMPLE`. Dummy RNC `000000000`, lab eNCF prefixes.

## Inbound lab command summary

`python manage.py dgii_inbound_xml_lab`:

- Default path: `tests/fixtures/dgii/inbound_lab/`
- `--path` for file or directory
- `--json` for parseable output
- `--fail-on-errors` optional exit code 1
- Prints `NOT_DGII_COMPLIANT`, `NON_OFFICIAL_SYNTHETIC_SAMPLE`, `not_certification_evidence=true`
- No DB mutation, no TrackId, no DGII calls

## Receiver contract update summary

Added to `get_receiver_contract_metadata()`:

- `inbound_xml_lab_available`: true
- `lab_mode`: NON_PRODUCTION_ONLY
- `synthetic_fixtures_available`: true
- `schema_validation`: NOT_CLAIMED
- `certification_evidence`: false

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no lab invocation from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- Blockers: **50** (7 new Phase 028 inbound lab blockers)

## Final pytest result

**263 passed** (was 239 at Phase 028 start).

## Remaining blockers (Phase 028 additions)

- `inbound_lab_synthetic_only`
- `inbound_schema_validation_not_claimed`
- `inbound_signature_verification_not_implemented`
- `inbound_persistence_not_implemented`
- `inbound_public_processing_disabled`
- `inbound_official_test_set_not_loaded`
- `inbound_lab_not_certification_evidence`

## Exact next recommended phase

**Phase 029 — Local inbound schema validation lab** — connect synthetic fixtures to local XSD for ECF/ARECF/ACECF offline; still no certification claim.
