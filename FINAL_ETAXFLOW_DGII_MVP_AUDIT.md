# Final eTaxFlow DGII MVP Audit

Date: 2026-08-09
Branch: `revamp/dgii-vault-mvp`
Scope: Phases 013–023

## Executive result

eTaxFlow is a usable internal, non-production invoice-vaulting and draft-generation MVP with local XSD feedback, test-only signing experiments, mocked DGII contracts, and a local certification-harness scaffold.

It is **NOT_DGII_COMPLIANT**. There were no live DGII calls, no DGII submission, no production XML claim, no real production signing, no private keys committed, and no certification evidence produced. `dgii_submission_allowed=false` remains the enforced boundary.

## Final verification

- `manage.py makemigrations --check`: no changes detected.
- `manage.py migrate --plan`: no planned migration operations.
- `manage.py check`: passed with no issues.
- `pytest -q`: **205 passed**.
- `seed_bcc`: completed; local warnings identify two pre-existing non-demo RNC values that do not satisfy the local XSD facet and were left unchanged.
- `diagnose_seed_duplicates`: no duplicate seed records detected.
- `inspect_dgii_mapping --internal-code BCC-AR-2026-000001`: Tipo 31 mapping is reviewed from six locally available sources but remains `REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT`; missing model/workflow fields include eNCF, FechaHoraFirma, and Signature.
- Unsigned Tipo 31 validation after explicit local demo preparation: `non_signature_structural_mismatch_count=0`, `facet_mismatch_count=0`, `signature_missing_expected_count=1`, `unknown_error_count=0`, `xsd_stub_informational_count=1`, and `unsigned_body_structurally_aligned_except_signature=true`.
- Readiness JSON: `overall_status=BLOCKED`, `compliance_status=NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, `dgii_call_made=false`, `track_id=null`, and `not_certification_evidence=true`.

The final unsigned validation required the explicit non-production commands `allocate_demo_encf --xsd-facet-demo --allow-demo --apply` and `prepare_signing_placeholder --apply`; `seed_bcc` intentionally does not authorize or allocate an eNCF by itself. Validation itself remained read-only.

## Architecture summary

- Django internal vaulting, fiscal master data, invoicing, audit events, and stored document metadata.
- Source-backed Tipo e-CF 31 field catalog and mapping groundwork.
- Non-production demo eNCF allocation with explicit `XSD_FACET_DEMO` provenance; it is not DGII authorization.
- Local unsigned XML draft generation and source-backed top-level structure comparison.
- Local XSD validation with an explicitly documented experimental stub for a local schema defect.
- Test-only XMLDSig sandbox with temporary key/certificate material that does not persist in the repository.
- Non-production deterministic printed PDF draft stored as a `Document` with hash/metadata and audit event.
- Mock-only DGII contract interfaces for authentication, reception, status, commercial approval, and receipt acknowledgment.
- Synthetic/sanitized local certification harness with `--no-submit` enforcement.
- Pre-certification readiness report and staging deployment/security planning documents.

## Implemented phases

| Phase | Result | Commit |
| --- | --- | --- |
| 013 | Demo facet hardening verified | `3eae78f` |
| 014 | Unsigned Tipo 31 structure diagnostics tightened | `85baa3f` |
| 015 | Signing threat model and key-management design | `af1d091` |
| 016 | Test-only XMLDSig sandbox | `60dfa2f` |
| 017 | Signed sandbox local XSD validation | `ac20029` |
| 018 | Non-production printed representation draft | `a1a6a2e` |
| 019 | Mocked DGII service contract layer | `1468ef5` |
| 020 | Local certification harness scaffold | `c98c008` |
| 021 | Pre-certification readiness report | `8fc736d` |
| 022 | Staging deployment plan | `b5e6972` |

## Safe internal MVP capabilities

- Vault and review internal invoice data.
- Maintain fiscal/master data and source-backed mappings.
- Generate local unsigned Tipo 31 draft XML for inspection.
- Compare the unsigned body against the local XSD sequence while explicitly treating Signature as omitted.
- Generate a test-only signed sandbox artifact only inside explicit test mode; it must never be submitted or treated as compliant.
- Generate and retain a clearly marked `NON_PRODUCTION_DRAFT` printed PDF.
- Exercise DGII-like service contracts through mocks only.
- Run synthetic/sanitized local certification cases with `--no-submit`.
- Review readiness blockers and staging controls.

## Commands available

Useful local-only commands include:

- `seed_bcc`
- `diagnose_seed_duplicates`
- `inspect_dgii_mapping --internal-code ...`
- `allocate_demo_encf --xsd-facet-demo --allow-demo --apply`
- `prepare_signing_placeholder --apply ...`
- `generate_tipo31_unsigned_draft --allow-demo-encf`
- `validate_tipo31_unsigned_draft --allow-demo-encf [--json]`
- `validate_tipo31_signed_sandbox --test-only --allow-demo-encf [--json]`
- `generate_tipo31_printed_draft --allow-demo-encf`
- `run_dgii_certification_harness --synthetic --no-submit`
- `dgii_readiness_report [--json]`

These commands are local workflow tools. None establishes DGII authorization, certification, approval, or production readiness.

## Remaining non-compliance and blockers

### Security and signing

- Production signing is unavailable by design.
- No production certificate/private-key custody, HSM/cloud signer, rotation/revocation process, access policy, recovery process, or approved signer exists.
- Real signing is disabled by default; the sandbox is test-only and uses ephemeral local material.
- Live DGII transport is not implemented and remains disabled.
- DGII endpoint placeholders are blank.
- Secrets-manager integration, operational audit retention, backup/restore evidence, and incident-response controls remain deployment work.

### XML and fiscal certification

- The unsigned draft intentionally omits Signature; this is the sole remaining structural error in the tested body, not a compliance result.
- Local validation uses an experimental in-memory XSD type stub because of a defect in the locally available schema source. This is informational and not official schema evidence.
- The eNCF used in the demo is synthetic/non-authorized, even when its shape is local-XSD-facet-safe.
- Five priority source documents are still missing locally; six of eleven expected sources are present.
- Official DGII authorization, OFV enrollment, Alta NCF/eNCF authorization, certification test execution, and acceptance evidence are absent.
- Printed PDF output is explicitly non-production; DGII-approved QR/security-code semantics are not implemented or asserted.

### Staging

- Staging deployment is documented but not deployed.
- Production credentials, live endpoints, production certificate material, and production data are prohibited.
- Network egress, access control, monitoring, backups/restore, rollback rehearsal, and operator approvals must be established before any staging release.

## Exact next human decisions

1. Confirm the legal/operational owner for OFV enrollment and access.
2. Confirm the authorized Alta NCF/eNCF process and ranges; provide approved source evidence.
3. Obtain and review the five missing DGII/legal/certification source documents.
4. Choose an approved production signing architecture: certificate custody, HSM/cloud/external signer, passphrase handling, access control, rotation, revocation, audit, and recovery.
5. Decide whether and when to authorize a separately isolated staging deployment; approve hosts, database, media, backup/restore, retention, egress, and rollback owners.
6. Define contingency, regularization, reconciliation, incident-response, and audit-retention policies.
7. Only after those decisions, define a human-controlled certification plan. Do not enable live DGII transport or claim compliance as part of this MVP work.

## Final safety statements

- **NOT_DGII_COMPLIANT.**
- No live DGII calls were made.
- No XML was submitted to DGII and no DGII TrackId was created.
- No production XML was generated or approved.
- No real production signing was implemented; only an explicitly test-only sandbox exists.
- No private keys, certificates, or passphrases were committed.
- This report and all local validation outputs are **not certification evidence**.
