# Non-Production Inbound XML Lab

**Phase:** 028  
**Status:** LAB_ONLY — not deployed, not DGII-compliant, not certification evidence  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`

## 1. Purpose

Controlled **local lab** for synthetic inbound XML (ECF, ARECF, ACECF). Internal classification, hashing, and reporting only:

- No public endpoint activation
- No DGII calls or TrackId creation
- No persistence to database
- No certification or compliance claim

## 2. Scope

| Fixture | Root | Notes |
|---|---|---|
| `synthetic_ecf_unsigned.xml` | ECF | No Signature element |
| `synthetic_ecf_signed_placeholder.xml` | ECF | Fake placeholder Signature |
| `synthetic_arecf_unsigned.xml` | ARECF | Acuse synthetic |
| `synthetic_arecf_signed_placeholder.xml` | ARECF | Fake placeholder Signature |
| `synthetic_acecf_unsigned.xml` | ACECF | Aprobación synthetic |
| `synthetic_acecf_signed_placeholder.xml` | ACECF | Fake placeholder Signature |
| `synthetic_unknown_root.xml` | UNKNOWNLABROOT | Unsupported root |
| `synthetic_invalid.xml` | — | Malformed XML |

Fixtures live in `tests/fixtures/dgii/inbound_lab/`.

## 3. Non-official fixture warning

All samples are marked **`NON_OFFICIAL_SYNTHETIC_SAMPLE`**.

- They are **not** DGII certification fixtures
- They are **not** evidence of compliance or schema validity
- They **must not** be submitted to DGII
- Dummy RNC (`000000000`) and lab eNCF prefixes (`LAB...`) are intentional

## 4. Lab pipeline

1. Read local fixture bytes (file or directory)
2. Safe parse (`lxml`, no external entities, no network)
3. Classify root tag (ECF / ARECF / ACECF / UNKNOWN / INVALID)
4. Detect `Signature` element presence (not verification)
5. Compute SHA-256 of raw bytes
6. Generate lab result dict
7. **No** DB write, **no** TrackId, **no** network

Command:

```bash
python manage.py dgii_inbound_xml_lab
python manage.py dgii_inbound_xml_lab --json
python manage.py dgii_inbound_xml_lab --path tests/fixtures/dgii/inbound_lab/synthetic_ecf_unsigned.xml --json
```

## 5. Result fields

Each analyzed fixture produces:

| Field | Description |
|---|---|
| `filename` | Source fixture name |
| `sha256` | SHA-256 of raw bytes |
| `root_tag` | Parsed root local name |
| `document_type` | ECF / ARECF / ACECF / UNKNOWN |
| `signature_present` | Boolean (presence only) |
| `status` | Classification status from receiver contract |
| `errors` | Error tokens (e.g. `signature_missing`, `invalid_xml`) |
| `compliance_status` | Always `NOT_DGII_COMPLIANT` |
| `dgii_submission_allowed` | Always `false` |
| `certification_evidence` | Always `false` |
| `track_id` | Always `null` |
| `persisted` | Always `false` |
| `dgii_call_made` | Always `false` |

## 6. Security notes

- Safe XML parser: entity expansion disabled, no external entity resolution, no network fetch during parse
- Do not log full XML bodies in production (future logging policy)
- Body size limits — future phase
- Persistence — not implemented; Phase 029 adds local XSD validation only, still no DB writes

## 7. Exit criteria

- [x] Internal lab command works (`dgii_inbound_xml_lab`)
- [x] Synthetic fixtures classified by root and signature presence
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/inbound_lab.py` — lab analysis functions
- `ecf/dgii/inbound_schema_lab.py` — Phase 029 local/offline XSD validation
- `docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md`
- `ecf/dgii/receiver.py` — classification helpers
- `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md`

`dgii_inbound_xml_lab` does **not** run XSD validation by default (`schema_validation_status=NOT_RUN_BY_DEFAULT`). Use `dgii_inbound_schema_lab` for local XSD results. A local XSD pass is not DGII acceptance.

## Next phase

**Phase 030 — Local inbound signature verification lab** — still non-production, no live DGII, no TrackId.
