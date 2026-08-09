# eTaxFlow Staging Security Baseline

This baseline applies to a future non-production staging deployment. It does not authorize production operation or live DGII traffic.

## Required controls

- Isolated account, project, network, database, storage, and DNS from production.
- HTTPS-only ingress, secure cookies, CSRF protection, HSTS after validation, and restricted administrative access.
- `DEBUG=false`, exact allowed hosts, dependency and image scanning, and no wildcard CORS/host policy.
- Least-privilege application/database/service accounts with MFA for operators.
- Secret-manager injection for Django secrets and future credentials; no secrets in source, images, logs, tickets, or checkpoints.
- Private media storage, encryption at rest and in transit, access logging, and sanitized test data.
- Centralized logs with redaction, retention, clock synchronization, alerting, and restricted access.
- Encrypted backups, restore testing, retention ownership, and documented rollback.
- Network egress deny-by-default for the application. In particular, no DGII live egress is permitted for this MVP.
- Review of migrations, permissions, dependencies, and security findings before release.

## Signing and DGII blockers

Production signing is blocked until certificate custody, approved signer/HSM or external signer design, passphrase handling, rotation/revocation, access control, audit events, and incident recovery are approved. No private key or certificate is stored in this repository. The mock DGII contracts and test-only XMLDSig sandbox are not production integration evidence.

Live DGII transport is not implemented and must remain disabled. The three DGII endpoint variables remain blank. No TrackId, authentication token, submission result, or approval may be fabricated or treated as live evidence.

## Incident response

On suspected secret exposure, unauthorized access, data leakage, or unexpected network traffic: isolate the staging workload, preserve redacted evidence, revoke/rotate affected credentials through the owner, block egress, assess media/database exposure, and document the decision. Do not attempt a live DGII retry as an incident response action.

## Review evidence

The deployment owner should retain evidence for configuration review, test results, backup/restore tests, access review, redaction checks, vulnerability review, and rollback rehearsal. These artifacts must not contain credentials, private keys, passphrases, or unredacted invoice data.
