# Pre-Certification Receiver Endpoint Contract

## 1. Purpose

This document defines the **internal contract** for future DGII-facing receiver endpoints in eTaxFlow. It is design-only:

- No live processing in Phase 027
- No production signing
- No DGII submission or TrackId creation
- No DGII compliance claim

Public routes remain **503 DISABLED** until explicit human approval, DNS/SSL verification, and security gates are satisfied.

## 2. Scope

| Route | Future role |
|---|---|
| `/fe/recepcion/api/ecf` | Receive inbound e-CF (ECF) XML |
| `/fe/aprobacioncomercial/api/ecf` | Receive Aprobación Comercial (ACECF) XML |
| `/fe/autenticacion/api/semilla` | Authentication seed placeholder |
| `/fe/autenticacion/api/validacioncertificado` | Certificate validation placeholder |

Authentication routes are placeholders in this contract; receiver XML processing focuses on ECF, ARECF, and ACECF roots.

## 3. Supported future XML root types

| Root tag | Document | Description |
|---|---|---|
| `ECF` | Electronic fiscal voucher | Inbound e-CF from counterparty or test harness |
| `ARECF` | Acuse de Recibo | Receipt acknowledgment response |
| `ACECF` | Aprobación Comercial | Commercial approval or rejection |

## 4. Current state

- Public route stubs return **503 DISABLED** JSON
- `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false` by default
- No database mutation from public routes
- No XML parse on disabled public routes
- No TrackId creation
- `compliance_status`: **NOT_DGII_COMPLIANT**
- Internal classification helpers exist in `ecf/dgii/receiver.py` for contract testing only

## 5. Future receiver pipeline design

Staged internal phases (not implemented in Phase 027):

1. **Raw request intake** — capture method, headers, body bytes, source channel
2. **Size / content-type check** — enforce body size cap and allowed content types
3. **Safe XML parser selection** — lxml with `resolve_entities=False`, `no_network=True`
4. **Root tag identification** — local name match for ECF / ARECF / ACECF
5. **Schema selection** — map root type to official XSD (future)
6. **Signature presence check** — detect XMLDSig `Signature` element
7. **Signature verification** — future only; production certs required
8. **Document hash** — SHA-256 of raw bytes for audit and duplicate detection
9. **Duplicate detection** — hash + eNCF + sender RNC (future)
10. **Storage as inbound document** — persist raw payload and metadata (future)
11. **Audit event** — immutable audit trail entry (future)
12. **Business workflow routing** — route to acuse/aprobación/ECF handlers (future)
13. **Response generation** — signed ARECF/ACECF or error response (future)

## 6. Non-production safety model

- Public endpoints disabled until explicit env flag and human gate
- Test-only internal service allowed for controlled lab XML (Phase 028+)
- No production certificates or private keys in repo
- No real counterparties or live DGII endpoints
- No DGII submission from receiver pipeline
- Staging / pre-certification / production environments remain separated

## 7. Error model

Future internal receiver statuses (design vocabulary):

| Status | Meaning |
|---|---|
| `RECEIVED_DISABLED` | Public route disabled; no processing |
| `RECEIVED_DESIGN_ONLY` | Contract/classification only; no persistence |
| `UNSUPPORTED_ROOT` | Unknown XML root element |
| `INVALID_XML` | Malformed or empty XML |
| `SCHEMA_NOT_CONFIGURED` | XSD mapping not available |
| `SIGNATURE_MISSING` | Required XMLDSig absent |
| `SIGNATURE_VERIFICATION_NOT_IMPLEMENTED` | Signature present but not verified |
| `DUPLICATE_DOCUMENT` | Hash or eNCF duplicate detected |
| `STORED_NON_PRODUCTION` | Stored for lab review only |
| `REJECTED_NON_PRODUCTION` | Rejected in non-production workflow |

Phase 027 implements classification statuses aligned with `ecf/dgii/receiver.py` enums only.

## 8. Data model proposal

Full inbound models are **not implemented** in Phase 027. Proposed future fields:

| Field | Purpose |
|---|---|
| `inbound_type` | ECF / ARECF / ACECF |
| `root_tag` | Parsed root local name |
| `source_channel` | PUBLIC_ROUTE / INTERNAL_LAB / IMPORT |
| `received_at` | UTC timestamp |
| `raw_sha256` | Hash of raw body |
| `filename` | Optional upload filename |
| `content_type` | Request Content-Type |
| `sender_rnc` | Extracted sender RNC (future) |
| `buyer_rnc` | Extracted buyer RNC (future) |
| `encf` | Extracted eNCF (future) |
| `signature_present` | Boolean |
| `signature_verified` | Boolean (future) |
| `schema_valid` | Boolean (future) |
| `status` | Internal workflow status |
| `rejection_reason` | Human/machine reason |
| `related_document_id` | FK to related invoice/document |
| `audit_event_id` | FK to audit trail |

## 9. Security controls

Required before enabling public receiver processing:

- Body size cap (configurable limit)
- XML entity expansion disabled; no external entity resolution
- No network fetch during XML parse
- Content-Type restrictions (`application/xml`, `text/xml`)
- Logging redaction (no full XML bodies in production logs)
- Rate limiting per source IP / RNC
- Audit trail for every accept/reject
- Replay / duplicate detection by hash and eNCF
- Staging isolation from production DB and secrets

## 10. Go / no-go

Do **not** enable public receiver processing until:

- [ ] DNS and TLS verified (Phase 026 checklist)
- [ ] Staging deployment approved
- [ ] Security owner approves receiver controls
- [ ] Tax/compliance owner approves workflow
- [ ] Production signing architecture approved (separate from lab)
- [ ] Phase 024 authorization gate signed off
- [ ] Readiness report reviewed — expect `BLOCKED` until implementation phases complete

## Related artifacts

- `ecf/dgii/receiver.py` — internal classification skeleton
- `ecf/management/commands/dgii_receiver_contract.py` — support matrix command
- `docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md` — portal URL design
- `docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md` — staging DNS/SSL checklist

- `ecf/dgii/inbound_lab.py` — non-production lab analysis (Phase 028)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md` — lab documentation
- `ecf/management/commands/dgii_inbound_xml_lab.py` — lab command
- `ecf/dgii/inbound_schema_lab.py` — local/offline XSD validation (Phase 029)
- `docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md` — schema lab documentation
- `ecf/dgii/inbound_signature_lab.py` — local/offline XMLDSig inspection (Phase 030)
- `docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md` — signature lab documentation
- `ecf/dgii/inbound_persistence_lab.py` — lab-only persistence (Phase 031)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md`

Local XSD validation is **LOCAL_OFFLINE_ONLY**. Signature lab is **LOCAL_OFFLINE_TEST_ONLY**. Persistence is **NON_PRODUCTION_LAB_ONLY** (dry-run default; no public-route writes). Public routes remain disabled. No DGII calls. No TrackId.

## Next phase

**Phase 032 — Non-production inbound workflow routing lab** — still no public endpoints, no DGII live, no TrackId.
