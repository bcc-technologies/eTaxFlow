# Non-Production Inbound Persistence Lab

**Phase:** 031  
**Status:** LAB_ONLY — persists synthetic analysis rows, not fiscal documents  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Persistence scope:** `NON_PRODUCTION_LAB_ONLY`

## 1. Purpose

Lab-only persistence for **synthetic inbound XML analysis records**.

- No public endpoint persistence
- No DGII calls, no TrackId
- No certification claim
- Default command mode is **DRY_RUN** (no DB write)

## 2. Scope

- Persist analysis records from synthetic inbound fixtures
- Persist classification, local schema, and signature-inspection summaries
- Do **not** persist production inbound traffic
- Do **not** touch invoice issuance or `ECFDocument` workflows
- Model: `ecf.InboundXMLLabRecord` — no FK to Invoice, Document, or ECFDocument

## 3. Boundary warning

- A persisted lab record ≠ received fiscal document
- A persisted lab record ≠ DGII acceptance
- A persisted lab record is **not** certification evidence
- No public route may create these records in Phase 031
- No TrackId may be created
- No production document lifecycle may be triggered

## 4. Data model

Implemented fields on `InboundXMLLabRecord`:

| Field | Notes |
|---|---|
| `id` | PK |
| `created_at` / `updated_at` | auto |
| `source_path` | fixture path |
| `filename` | fixture name |
| `raw_sha256` | unique, indexed |
| `raw_size_bytes` | payload length |
| `root_tag` / `document_type` | classification |
| `classification_status` | receiver status |
| `signature_present` | boolean |
| `signature_verification_status` | inspection status |
| `signature_verified` | always false |
| `production_signature_ready` | always false |
| `schema_validation_scope` | LOCAL_OFFLINE_ONLY |
| `xsd_path` / `xsd_available` / `xsd_compiled` | schema lab |
| `local_xsd_valid` / `xsd_error_count` | schema lab |
| `errors_json` | merged lab errors |
| `persisted_raw_xml` | default false |
| `raw_xml_text` | empty unless `--store-raw-lab-xml` |
| `compliance_status` | NOT_DGII_COMPLIANT |
| `dgii_submission_allowed` | false |
| `certification_evidence` | false |
| `track_id` | null |
| `dgii_call_made` | false |
| `lab_mode` | NON_PRODUCTION_LAB_ONLY |

## 5. Lab pipeline

1. Read synthetic XML fixture bytes
2. Run inbound XML lab
3. Run local schema lab
4. Run local signature lab
5. Assemble payload and hash
6. Deduplicate by `raw_sha256` (`update_or_create`)
7. Persist **only** with `--persist-lab-records`
8. No public route, no DGII, no TrackId

```bash
python manage.py dgii_inbound_persistence_lab
python manage.py dgii_inbound_persistence_lab --json
python manage.py dgii_inbound_persistence_lab --persist-lab-records --json
python manage.py dgii_inbound_persistence_lab --path tests/fixtures/dgii/inbound_lab/synthetic_ecf_unsigned.xml --persist-lab-records --json
```

## 6. Deduplication

`raw_sha256` is unique. Re-running persist upserts the same row. `--allow-duplicates` is accepted but the unique hash still upserts (no true duplicates).

## 7. Security notes

- Default avoids raw XML storage
- `--store-raw-lab-xml` required to store text; sets `persisted_raw_xml=true`
- Keep model outside production document workflow
- No real taxpayer data
- Public views must not import this service

## 8. Exit criteria

- [x] Persistence command works (dry-run default)
- [x] JSON output parseable
- [x] Records are lab-only
- [x] Deduplication by hash
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/models.py` — `InboundXMLLabRecord`
- `ecf/dgii/inbound_persistence_lab.py`
- `ecf/management/commands/dgii_inbound_persistence_lab.py`

## Next phase

**Phase 032 — Non-production inbound workflow routing lab** — still no public endpoints, no DGII live, no TrackId.
