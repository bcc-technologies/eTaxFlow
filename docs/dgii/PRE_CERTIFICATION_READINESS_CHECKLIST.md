# DGII Pre-Certification Readiness Checklist

## Current status

The local report is intentionally **BLOCKED** and **NOT_DGII_COMPLIANT**. It
is an operational gap report, not certification evidence. Run:

```text
.venv/bin/python manage.py dgii_readiness_report
.venv/bin/python manage.py dgii_readiness_report --json
```

## Checklist

| Area | Current status | Required human/engineering action |
|---|---|---|
| Software name/version/type | READY (local metadata) | Confirm final registration metadata. |
| URL Recepción | BLOCKED | Obtain and approve environment-specific endpoint. |
| URL Aprobación Comercial | BLOCKED | Obtain and approve environment-specific endpoint. |
| URL Autenticación | BLOCKED | Obtain and approve environment-specific endpoint. |
| RNC readiness | PARTIAL | Verify issuer RNC and taxpayer records with the owner. |
| OFV readiness | MANUAL_REQUIRED | Confirm OFV enrollment, access, and responsible operator. |
| Alta NCF | MANUAL_REQUIRED | Confirm authorized NCF/eNCF range workflow and records. |
| Certificate readiness | BLOCKED | Select custody, certificate, rotation, and revocation process. |
| Signing readiness | BLOCKED | Complete approved XMLDSig architecture and signer integration. |
| XML validation | PARTIAL | Resolve source/stub limitations and perform authoritative review. |
| Printed representation | PARTIAL | Review official representation requirements and source-backed QR/security data. |
| Contingency | NOT_IMPLEMENTED | Design and test contingency/regularization/reconciliation workflow. |
| Logs/audit retention | PARTIAL | Define retention, export, monitoring, and review controls. |
| Backups | NOT_IMPLEMENTED | Implement encrypted backups, restore tests, and recovery ownership. |
| Secrets handling | PARTIAL | Integrate a deployment secret manager and redaction controls. |
| Security blockers | BLOCKED | Close live transport, signing, certificate, authorization, and access-control gaps. |

## Remaining documentation

The command reads `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md` through the local
inventory helper. Missing legal/service/certification sources remain blocked
until a human provides and reviews authoritative copies. Official certification
test cases must not be invented.

## Explicit non-claims

- No DGII endpoint is called.
- No TrackId is created.
- Local mock contracts and test-only signatures do not satisfy certification.
- A local XSD or PDF result does not establish DGII approval.
