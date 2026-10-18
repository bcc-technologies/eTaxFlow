# eTaxFlow Render Staging Deployment

Status: **controlled staging readiness only** — this document does not deploy, push, merge, enable DGII, or authorize certification.

Compliance boundary: `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false` · public `/fe/...` routes remain **503 DISABLED**.

## Chosen compute plan

| Resource | Plan | Rationale |
| --- | --- | --- |
| Web Service | **Starter** (single instance) | Always-on process for controlled health checks; Free spin-down is unsuitable for a deliberate staging gate. |
| PostgreSQL | **Basic-256MB** (or current Render Basic equivalent) | Dedicated non-production database via `DATABASE_URL`; no SQLite in staging. |
| Region | Match DNS/owner preference | Keep web + Postgres in the same region. |

Unresolved until a human owner confirms in Render: exact service name, exact Postgres plan SKU, custom-domain cutover ticket, and whether Pre-Deploy Command is enabled on the billing plan. Do not invent credentials.

## Exact Render Web Service fields

| Field | Value |
| --- | --- |
| Name | `etaxflow-staging` (example; owner may rename) |
| Runtime | `Python 3` |
| Branch | `revamp/dgii-vault-mvp` |
| Root Directory | _(empty — repository root)_ |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Pre-Deploy Command | `python manage.py migrate --noinput` |
| Start Command | `gunicorn etaxflow.wsgi:application --bind 0.0.0.0:$PORT` |
| Health Check Path | `/healthz` |
| Auto-Deploy | **Off** for the first controlled deploy (manual deploy only) |
| Instances | **1** |

If Pre-Deploy Command is unavailable on the billing plan, use this **single-instance** start command instead (do not use with multiple instances):

```bash
python manage.py migrate --noinput && gunicorn etaxflow.wsgi:application --bind 0.0.0.0:$PORT
```

## Safe migration strategy (Starter, single instance)

1. Keep **one** web instance only while schema changes are applied.
2. Prefer **Pre-Deploy Command** `python manage.py migrate --noinput` so migrations finish before traffic is routed to the new release.
3. If Pre-Deploy is unavailable, run migrate in the start command **only** while instances=1.
4. Do not migrate from an ad-hoc shell against production-like data without a reviewed release note.
5. Roll back by redeploying the previous successful release artifact; restore the Render Postgres backup if a forward migration is not reverse-compatible.
6. Never enable DGII or signing as part of a migration.

## Hostnames

| Host | Purpose |
| --- | --- |
| `<service>.onrender.com` | Render default hostname (replace with actual service hostname after create) |
| `etaxflow.bcctechnologies.com.do` | Approved custom domain (DNS/TLS still human-owned; see `DGII_STAGING_DNS_SSL_CHECKLIST.md`) |

Set both in `ALLOWED_HOSTS`. Set HTTPS origins (not bare hosts) in `CSRF_TRUSTED_ORIGINS`.

## Environment variables (staging)

Inject via Render Environment / Secret File. **Do not commit real values.** Placeholders only:

| Variable | Staging value |
| --- | --- |
| `DEBUG` | `false` |
| `SECRET_KEY` | Unique random staging secret (Render secret / secret manager) |
| `DATABASE_URL` | From Render PostgreSQL (**Internal Database URL**) |
| `DATABASE_SSL_REQUIRE` | `true` |
| `ALLOWED_HOSTS` | `<service>.onrender.com,etaxflow.bcctechnologies.com.do` |
| `CSRF_TRUSTED_ORIGINS` | `https://<service>.onrender.com,https://etaxflow.bcctechnologies.com.do` |
| `SECURE_SSL_REDIRECT` | `true` |
| `SESSION_COOKIE_SECURE` | `true` |
| `CSRF_COOKIE_SECURE` | `true` |
| `SECURE_HSTS_SECONDS` | `0` until security owner approves staging HSTS |
| `MEDIA_ROOT` | `/var/data/media` if a disk is attached; otherwise a private ephemeral path with the understanding that uploads are not durable on Starter without a disk |
| `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS` | `false` |
| `ETAXFLOW_PUBLIC_BASE_URL` | blank until DNS/TLS approved |
| `DGII_ENVIRONMENT` | `MOCK` |
| `DGII_LIVE_TRANSPORT_ENABLED` | `false` |
| `DGII_URL_AUTENTICACION` | blank |
| `DGII_URL_RECEPCION` | blank |
| `DGII_URL_APROBACION_COMERCIAL` | blank |
| `SIGNING_MODE` | `DISABLED` |
| `SIGNING_BACKEND` | `NONE` (app placeholder only; Django keeps its default cookie signer) |
| `SIGNING_ENABLED` | `false` |
| `SIGNING_ALLOW_TEST_ONLY` | `false` |
| `SIGNING_CERT_PATH` | blank |
| `SIGNING_KEY_PATH` | blank |
| `SIGNING_PASS_ENV_VAR` | blank |

Django also trusts `X-Forwarded-Proto` via `SECURE_PROXY_SSL_HEADER` (code default) because Render terminates TLS at the edge.

## Post-deploy smoke checks (manual, after a human deploys)

Do **not** run these from CI against a live DGII network. After a controlled deploy:

```bash
curl -fsS "https://<service>.onrender.com/healthz"
# expect: HTTP 200 body "ok"

curl -i -X POST "https://<service>.onrender.com/fe/recepcion/api/ecf" \
  -H "Content-Type: application/xml" \
  --data '<ECF/>'
# expect: HTTP 503 JSON status=DISABLED, track_id=null — no fiscal processing
```

Repeat the 503 check for:

- `/fe/aprobacioncomercial/api/ecf`
- `/fe/autenticacion/api/semilla`
- `/fe/autenticacion/api/validacioncertificado`

## Explicit non-goals

- No deploy, push, or merge to `main` from this document.
- No real fiscal data, credentials, certificates, or private keys in the repository or examples.
- No enabling of public DGII endpoints, live transport, or signing.
- No claim of DGII compliance or certification evidence.
