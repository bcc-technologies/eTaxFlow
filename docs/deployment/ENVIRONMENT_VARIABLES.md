# eTaxFlow Environment Variables

These variables describe deployment configuration. Values must be supplied by the deployment secret/configuration system, not committed to source. The repository defaults are local-development or mock-safe defaults.

## Django and storage

| Variable | Staging guidance |
| --- | --- |
| `DEBUG` | Set `false`. |
| `ALLOWED_HOSTS` | Comma-separated exact staging hosts; never `*`. |
| `DATABASE_URL` | Secret-manager reference or injected credential for the dedicated staging database. |
| `MEDIA_ROOT` | Private, dedicated staging storage path. |
| `SECRET_KEY` | Inject a unique random staging value; never use a repository example value. |
| `CSRF_TRUSTED_ORIGINS` | Exact `https://` staging origins only. |

## DGII contract layer

| Variable | Safe repository/staging value |
| --- | --- |
| `DGII_ENVIRONMENT` | `MOCK` |
| `DGII_SOFTWARE_NAME` | `eTaxFlow` |
| `DGII_SOFTWARE_VERSION` | `MVP` |
| `DGII_SOFTWARE_TYPE` | `INTERNAL` |
| `DGII_URL_AUTENTICACION` | Blank until a separately approved future integration. |
| `DGII_URL_RECEPCION` | Blank until a separately approved future integration. |
| `DGII_URL_APROBACION_COMERCIAL` | Blank until a separately approved future integration. |
| `DGII_LIVE_TRANSPORT_ENABLED` | `false` |

## Signing placeholders

| Variable | Safe repository/staging value |
| --- | --- |
| `SIGNING_MODE` | `DISABLED` |
| `SIGNING_BACKEND` | `NONE` |
| `SIGNING_ENABLED` | `false` |
| `SIGNING_ALLOW_TEST_ONLY` | `false` by default; enable only inside a disposable test job. |
| `SIGNING_CERT_PATH` | Blank. Do not point at a committed or shared certificate. |
| `SIGNING_KEY_PATH` | Blank. Do not point at a committed private key. |
| `SIGNING_PASS_ENV_VAR` | Blank. Never put a passphrase in this file. |

## Handling rules

- `.env.staging.example` is a placeholder template, not a credential source.
- Real values belong in an approved secret manager or protected deployment configuration.
- Do not print the environment, dump settings, or include these values in tickets/logs.
- Rotate leaked values immediately and review access logs.
- Blank DGII endpoints and disabled transport are intentional blockers, not missing setup to be silently filled.
