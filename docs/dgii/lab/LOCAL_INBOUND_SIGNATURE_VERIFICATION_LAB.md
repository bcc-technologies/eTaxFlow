# Local Inbound Signature Verification Lab

**Phase:** 030  
**Status:** LAB_ONLY — local/offline XMLDSig inspection, not DGII-compliant, not certification evidence  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Verification scope:** `LOCAL_OFFLINE_TEST_ONLY`  
**Cryptographic XMLDSig verification:** `NOT_IMPLEMENTED`

## 1. Purpose

Local/offline XMLDSig **inspection** lab for synthetic inbound XML (ECF, ARECF, ACECF).

- No real DGII certificates
- No production signing
- No private keys in the repository
- No DGII call, no TrackId, no public endpoint activation
- No certification claim

## 2. Scope

| Case | Behavior |
|---|---|
| Unsigned synthetic samples | `signature_present=false`, status `MISSING` |
| Placeholder Signature (`<Signature><SignedInfo/></Signature>`) | `PLACEHOLDER_ONLY`, never valid |
| Structurally complete Signature without a safe verifier | `VERIFICATION_NOT_IMPLEMENTED` |
| Invalid XML | `PARSE_ERROR` |
| Optional test-only cryptographic verify | Not implemented; `signxml` is not a project dependency |

## 3. Boundary warning

- Signature present ≠ signature valid
- Test-only inspection ≠ DGII acceptance
- Local signature lab ≠ certification
- No private key may be committed
- No production certificate may be used
- No CRL/OCSP/network validation in this phase

## 4. Lab pipeline

1. Read synthetic XML bytes
2. Safe parse (`no_network`, no entity resolution)
3. Classify root (reuse `inbound_lab.analyze_inbound_xml`)
4. Detect `Signature` element
5. Extract namespace / SignatureMethod / DigestMethod / X509Certificate presence
6. Classify PLACEHOLDER_ONLY vs MISSING vs NOT_IMPLEMENTED
7. Do **not** claim cryptographic validity
8. Generate lab result
9. **No** DB write, **no** TrackId, **no** DGII call

```bash
python manage.py dgii_inbound_signature_lab
python manage.py dgii_inbound_signature_lab --json
python manage.py dgii_inbound_signature_lab --path tests/fixtures/dgii/inbound_lab/synthetic_ecf_signed_placeholder.xml --json
python manage.py dgii_inbound_signature_lab --summary-only
```

`dgii_inbound_xml_lab` and `dgii_inbound_schema_lab` do **not** run signature verification by default.

## 5. Result fields

| Field | Description |
|---|---|
| `filename` | Source fixture name |
| `sha256` | SHA-256 of raw bytes |
| `root_tag` | Parsed root local name |
| `document_type` | ECF / ARECF / ACECF / UNKNOWN |
| `signature_present` | Boolean |
| `signature_namespace` | XMLDSig namespace if present |
| `signature_algorithm` | SignatureMethod Algorithm if present |
| `digest_algorithm` | DigestMethod Algorithm if present |
| `certificate_present` | X509Certificate element with text |
| `certificate_subject_summary` | Only if safely parseable (currently unused; no cert parser) |
| `verification_scope` | Always `LOCAL_OFFLINE_TEST_ONLY` |
| `signature_verification_status` | See vocabulary below |
| `signature_verified` | Always `false` in this phase |
| `signature_errors` | Tokens / reasons |
| `production_signature_ready` | Always `false` |
| `compliance_status` | Always `NOT_DGII_COMPLIANT` |
| `dgii_submission_allowed` | Always `false` |
| `certification_evidence` | Always `false` |
| `track_id` | Always `null` |
| `persisted` | Always `false` |
| `dgii_call_made` | Always `false` |

## 6. Signature status vocabulary

| Status | Meaning |
|---|---|
| `MISSING` | No Signature element |
| `PLACEHOLDER_ONLY` | Signature present but empty / no SignatureValue+DigestValue |
| `UNSUPPORTED_SIGNATURE_FORMAT` | Signature namespace is not XMLDSig |
| `VERIFICATION_NOT_IMPLEMENTED` | Structurally complete but no safe verifier |
| `TEST_ONLY_VALID` | Reserved; not produced in Phase 030 |
| `TEST_ONLY_INVALID` | Reserved for future test-only verifier failures |
| `PARSE_ERROR` | XML could not be parsed |

## 7. Security notes

- Safe XML parser; no external entity resolution; no network fetch
- No private key in repo
- No real taxpayer certificate
- No production trust-chain validation
- Logs must not contain full certificates or signatures in production
- Tests must not write private keys to disk (`tests/helpers/test_only_xmldsig.py` documents skip)

## 8. Exit criteria

- [x] Command `dgii_inbound_signature_lab` works
- [x] JSON output parseable
- [x] Placeholder signatures are not reported as valid
- [x] Missing signatures are reported cleanly
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/dgii/inbound_signature_lab.py`
- `ecf/management/commands/dgii_inbound_signature_lab.py`
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md`
- `docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md`

## Next phase

**Phase 031 — Non-production inbound persistence lab** — still no public endpoints, no DGII live, no TrackId.
