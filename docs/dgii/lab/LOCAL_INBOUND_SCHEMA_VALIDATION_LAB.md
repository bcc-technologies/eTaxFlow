# Local Inbound Schema Validation Lab

**Phase:** 029  
**Status:** LAB_ONLY — local/offline XSD validation, not DGII-compliant, not certification evidence  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Schema scope:** `LOCAL_OFFLINE_ONLY`

## 1. Purpose

Local/offline XSD validation for **synthetic inbound XML lab files** from Phase 028.

- Validation is local only (files under `docs/dgii/sources/`)
- No DGII call, no TrackId, no public endpoint activation
- No certification claim
- No production compliance claim
- A local XSD pass does **not** equal DGII acceptance

## 2. Scope

| Case | Behavior |
|---|---|
| ECF | Validate against local Tipo 31 XSD (`e-CF_31_v1.0.xsd`) |
| ARECF | Validate against local `ARECF_v1.0.xsd` |
| ACECF | Validate against local `ACECF_v1.0.xsd` |
| Invalid XML | Clean `invalid_xml` / `local_xsd_valid=false` |
| Unsupported root | `xsd_available=false`, unmapped |
| Missing XSD | `xsd_available=false`, no crash |

## 3. XSD mapping

Repo filenames used (under `docs/dgii/sources/`):

| Document type | Local file | Notes |
|---|---|---|
| ECF | `e-CF_31_v1.0.xsd` | Current lab maps **Tipo 31 only**. No TipoeCF detector yet. Other e-CF XSDs (32–47) are present but unused here. |
| ARECF | `ARECF_v1.0.xsd` | Present in repo |
| ACECF | `ACECF_v1.0.xsd` | Present in repo |
| UNKNOWN | none | Unmapped |

## 4. Boundary warning

- Local XSD valid ≠ DGII acceptance
- Synthetic XML valid ≠ certification
- Placeholder `Signature` ≠ valid XMLDSig
- Known source defects or compile errors are **reported**, not hidden
- Official XSD files are **not** modified in this phase
- Current observation: local `e-CF_31_v1.0.xsd` may fail to compile (`IndicadorServicioTodoIncluidoType` unresolved). The lab reports this instead of claiming a pass.

## 5. Lab pipeline

1. Read local synthetic fixture bytes
2. Classify root (reuse `inbound_lab.analyze_inbound_xml`)
3. Choose local XSD by document type
4. Compile local XSD with `lxml` (`no_network=True`, no entity resolution)
5. Validate XML against local XSD
6. Collect validation errors
7. Generate lab result
8. **No** DB write, **no** TrackId, **no** DGII call

```bash
python manage.py dgii_inbound_schema_lab
python manage.py dgii_inbound_schema_lab --json
python manage.py dgii_inbound_schema_lab --path tests/fixtures/dgii/inbound_lab/synthetic_ecf_unsigned.xml --json
python manage.py dgii_inbound_schema_lab --summary-only
```

`dgii_inbound_xml_lab` remains classification-only (`schema_validation_status=NOT_RUN_BY_DEFAULT`).

## 6. Result fields

| Field | Description |
|---|---|
| `filename` | Source fixture name |
| `sha256` | SHA-256 of raw bytes |
| `root_tag` | Parsed root local name |
| `document_type` | ECF / ARECF / ACECF / UNKNOWN |
| `signature_present` | Boolean (presence only) |
| `signature_verified` | Always `false` in this phase |
| `xsd_path` | Local XSD path or null |
| `xsd_available` | File exists |
| `xsd_compiled` | Local compile succeeded |
| `local_xsd_valid` | Instance valid against local XSD |
| `xsd_error_count` | Number of reported local errors |
| `xsd_errors` | Truncated local error messages |
| `schema_validation_scope` | Always `LOCAL_OFFLINE_ONLY` |
| `compliance_status` | Always `NOT_DGII_COMPLIANT` |
| `dgii_submission_allowed` | Always `false` |
| `certification_evidence` | Always `false` |
| `track_id` | Always `null` |
| `persisted` | Always `false` |
| `dgii_call_made` | Always `false` |

## 7. Expected synthetic fixture behavior

Phase 028 fixtures are **deliberately minimal**. Some or all will be **locally XSD-invalid**. That is acceptable.

Tests verify **honest reporting**, not fake validity.

## 8. Exit criteria

- [x] Command `dgii_inbound_schema_lab` works
- [x] JSON output parseable
- [x] Local XSD mapping reported
- [x] Local validation errors reported cleanly
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/inbound_schema_lab.py`
- `ecf/management/commands/dgii_inbound_schema_lab.py`
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md`
- `docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md` (Phase 030 — inspection only; presence ≠ valid)
- `tests/fixtures/dgii/inbound_lab/`
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md` (Phase 031 — lab-only persistence)

Signature verification is **not** run by `dgii_inbound_schema_lab` (`signature_verification_status=NOT_RUN_BY_DEFAULT`). Persistence is a separate command (`persistence_status=NOT_RUN_BY_DEFAULT`). Workflow routing is a separate command (`workflow_status=NOT_RUN_BY_DEFAULT`).

## Next phase

**Phase 033 — Non-production inbound audit and retention policy lab** — still no public endpoints, no DGII live, no TrackId.
