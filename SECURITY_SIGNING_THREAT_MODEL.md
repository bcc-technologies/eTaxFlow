# Signing Threat Model — eTaxFlow

## Security position

eTaxFlow currently has no production signing capability. The signing placeholder
only supplies local `FechaHoraFirma` workflow data and is not XMLDSig. The
system remains `NOT_DGII_COMPLIANT`; this threat model does not change that
status.

## Assets

- Private signing keys and their protection boundary.
- Certificate chains, fingerprints, and validity metadata.
- Passphrases and secret-manager credentials.
- Unsigned and future signed invoice XML.
- Invoice identity, eNCF, audit history, and signer decisions.
- Availability and integrity of the signer and its verification results.

## Trust boundaries

1. Django application and database.
2. Local filesystem/media and backups.
3. Runtime environment and process supervisor.
4. Human operators and administrators.
5. Future HSM/KMS or external signer.
6. Future DGII transport boundary (out of scope and disabled here).

## Threats and controls

| Threat | Impact | Required control |
|---|---|---|
| Private key committed to Git | Key compromise and unauthorized e-CF signing | Secret scanning, ignored temporary paths, review gate, no key persistence in models |
| Key leaked through logs or exceptions | Key compromise | Redaction middleware, structured allowlists, no secret values in error text |
| Passphrase in environment/history | Signer compromise | Secret manager, short-lived references, no `.env` secrets, fail-closed startup |
| Wrong certificate or expired chain | Invalid or rejected documents | Fingerprint/validity/key-usage checks and verification before signing |
| XML altered after signing | Integrity failure or rejection | Sign exact canonical bytes, verify before transport, immutable artifact metadata |
| Replay or duplicate signing | Duplicate fiscal artifacts | Idempotency key, invoice state machine, audit correlation, signer-side replay controls |
| Unauthorized operator signs | Fraud or policy violation | Least privilege, approval workflow, signer ACLs, audit review |
| Test signature reaches production | False compliance or rejection | Explicit test-only marker, transport guard, production mode default disabled |
| HSM/KMS unavailable | Operational outage | Timeout, retry policy, no unsafe fallback, reconciliation and alerting |
| Revoked key remains active | Trust failure | Revocation checks, rotation runbook, emergency disable switch |
| Backup exposes signer material | Long-lived compromise | Separate key custody, encrypted metadata backups, restore tests |
| DGII endpoint is called prematurely | External side effect/compliance risk | No live transport, no production URLs, explicit future certification gate |

## Required invariants

- No private key or certificate secret is stored in Django models.
- No passphrase is stored in Django models, settings defaults, checkpoints, or
  logs.
- Real signing fails unless an explicit, reviewed mode is enabled.
- Test-only signatures are visibly marked and never considered compliant.
- A signing failure cannot set an accepted/submitted state.
- Audit records identify outcomes without exposing secrets.
- The application cannot create a TrackId locally by pretending to call DGII.

## Failure and incident response

On suspected key exposure: disable the signer, revoke/rotate the certificate,
preserve redacted audit evidence, inspect logs and backups, and require a new
approval before re-enabling. On XML verification failure: quarantine the
artifact, do not submit it, retain the diagnostic without key material, and
reconcile invoice state manually.

## Open decisions before production

- HSM/KMS versus external signing service.
- Authoritative XMLDSig profile and verification library.
- Certificate procurement, custody, rotation, and revocation owner.
- Secret-manager and deployment integration.
- Approval and segregation-of-duties workflow.
- Retention and incident-response requirements.

Until those decisions are closed and separately certified, production signing
is blocked.
