# eTaxFlow Staging Deployment Plan

Status: planning only — staging is not deployed by this repository.

## Purpose and boundary

Staging is an isolated environment for internal MVP workflow testing, local XML/PDF review, audit review, and mocked DGII contract testing. It must not submit documents to DGII, request a TrackId from DGII, or use production certificates, credentials, or endpoints. The application remains `NOT_DGII_COMPLIANT` until a separate human-controlled certification and production authorization milestone.

## Django application

- Run with a dedicated staging settings configuration or environment variables.
- Set `DEBUG=false`.
- Set `ALLOWED_HOSTS` to the exact staging hostnames; never use `*`.
- Enforce secure cookies, CSRF origin checks, HSTS, and HTTPS at the reverse proxy and Django layer.
- Run `manage.py check --deploy` as part of release review.
- Run migrations as a reviewed release step; do not migrate from an unreviewed shell.
- Use a dedicated non-production database and service account.
- Keep `DGII_ENVIRONMENT=MOCK` and `DGII_LIVE_TRANSPORT_ENABLED=false`.
- Keep signing disabled unless an explicitly isolated test-only sandbox test requires it.

## HTTPS and routing

Terminate HTTPS at an approved reverse proxy or load balancer. Redirect HTTP to HTTPS, forward only required headers, and restrict administrative routes by network and identity controls. Staging DNS and certificates must be distinct from production. No live DGII URL belongs in the staging example configuration.

## Database and media

Use a dedicated staging database with least-privilege credentials and encryption at rest where available. Media storage must be private by default, access-controlled, and separated from production. Uploaded documents can contain sensitive invoice data; do not copy production data into staging unless it has been sanitized and approved. Generated XML/PDF drafts remain non-production artifacts.

## Backups and rollback

Before each release, take an encrypted staging database backup and record its retention period. Test restore procedures on a schedule. A rollback consists of disabling the release, restoring the prior application artifact, applying only a reviewed reverse-compatible migration plan, and restoring the database backup if data integrity requires it. Certificate/private-key backup and recovery are intentionally out of scope until an approved production signing design exists.

## Logging and audit

Centralize application and reverse-proxy logs with access controls, clock synchronization, retention, and deletion rules. Redact tokens, credentials, cookies, authorization headers, certificate paths, key paths, and invoice-sensitive payloads. Preserve application `AuditEvent` records according to an approved retention policy. Logs must show that mock/test-only operations are not DGII submissions.

## Future DGII routing

The future service routing slots are `DGII_URL_AUTENTICACION`, `DGII_URL_RECEPCION`, and `DGII_URL_APROBACION_COMERCIAL`. They remain blank in staging. Enabling a live transport requires a separate security review, approved endpoint allow-list, credential custody, certificate/signing readiness, monitoring, and an explicit human authorization; this plan does not grant that authorization.

## Health checks

The deployment should expose an authenticated or non-sensitive health check that verifies process availability and database connectivity without exposing invoice content, secrets, configuration values, or DGII credentials. Readiness must fail closed when required staging dependencies are unavailable.

## Release gates

1. Review source, migrations, dependency lock state, and security findings.
2. Build from a reproducible artifact and scan it for secrets and unexpected files.
3. Apply the staging environment policy and verify `check --deploy`.
4. Run the full test suite and local validation/harness commands with network access disabled.
5. Confirm backups, restore evidence, log redaction, access review, and rollback owner.
6. Record explicit human approval for staging use; do not infer production approval.
