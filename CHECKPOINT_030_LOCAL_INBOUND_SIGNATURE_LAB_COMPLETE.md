# Checkpoint 030 — Local Inbound Signature Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`46ebd21` — Add local inbound schema validation lab

## Files changed

- `CHECKPOINT_030_LOCAL_INBOUND_SIGNATURE_LAB_START.md` (new)
- `CHECKPOINT_030_LOCAL_INBOUND_SIGNATURE_LAB_COMPLETE.md` (new)
- `docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md` (new)
- `ecf/dgii/inbound_signature_lab.py` (new)
- `ecf/dgii/inbound_signature_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_signature_lab.py` (new)
- `tests/test_dgii_inbound_signature_lab.py` (new)
- `tests/helpers/test_only_xmldsig.py` (new — documents skip, no keys)
- `tests/helpers/__init__.py` (new)
- Updates: inbound XML/schema labs, receiver contract, readiness report, README and related docs

## Migrations

No changes detected.

## Signature lab documentation created

`docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md`

## Signature inspection summary

Synthetic fixtures:

- Unsigned ECF/ARECF/ACECF → `MISSING`
- Signed-placeholder ECF/ARECF/ACECF → `PLACEHOLDER_ONLY` (`signature_verified=false`)
- Invalid XML → `PARSE_ERROR`
- Unknown root → no crash, `MISSING`

## Verification behavior summary

Inspection extracts namespace / SignatureMethod / DigestMethod / X509Certificate presence. Placeholders have empty `SignedInfo` and no `SignatureValue`/`DigestValue`.

## Cryptographic XMLDSig verification

**NOT_IMPLEMENTED.** There is no safe existing verifier in-repo and `signxml` is not a dependency. Tests do not generate or commit private keys. `TEST_ONLY_VALID` is never produced.

## Private key safety check result

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` matched only pre-existing `.conda/.../api-ms-win-crt-private-l1-1-0.dll` (Windows CRT DLL name). **False positive.** No `.pem`/`.p12`/`.pfx`/`.key` private key files added in this phase.

## Receiver contract update summary

- `local_inbound_signature_lab_available`: true
- `signature_verification_scope`: LOCAL_OFFLINE_TEST_ONLY
- `signature_verification_command`: dgii_inbound_signature_lab
- `production_signature_ready`: false
- `signature_verification`: NOT_IMPLEMENTED
- `persistence`: NOT_IMPLEMENTED
- `public_endpoints_enabled`: false

XML/schema labs report `signature_verification_status=NOT_RUN_BY_DEFAULT`.

## Public route status

All `/fe/...` stubs remain **503 DISABLED**. No XML parse, no signature lab invocation from public views.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `production_signature_ready`: **false**
- `dgii_call_made`: **false**
- `track_id`: **null**
- Blockers: **65** (7 new Phase 030 signature lab blockers)

## Final pytest result

**309 passed** (was 286 at Phase 030 start).

## Remaining blockers (Phase 030 additions)

- `local_inbound_signature_lab_only`
- `signature_presence_not_signature_validity`
- `production_signature_verification_not_implemented`
- `certificate_trust_chain_validation_not_implemented`
- `revocation_check_not_implemented`
- `official_certificate_policy_not_approved`
- `inbound_signature_results_not_certification_evidence`

Plus prior Phase 024–029 blockers (including `inbound_public_processing_still_disabled` and `inbound_persistence_still_not_implemented`).

## Exact next recommended phase

**Phase 031 — Non-production inbound persistence lab** — still no public endpoints, no DGII live, no TrackId, no production signing.
