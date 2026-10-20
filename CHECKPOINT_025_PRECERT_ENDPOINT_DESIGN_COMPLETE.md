# Checkpoint 025 — Pre-Certification Endpoint Design Complete

## Branch

`revamp/dgii-vault-mvp`

## Files changed

### Added
- `CHECKPOINT_025_PRECERT_ENDPOINT_DESIGN_START.md`
- `CHECKPOINT_025_PRECERT_ENDPOINT_DESIGN_COMPLETE.md`
- `docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md`
- `ecf/dgii/endpoints.py`
- `ecf/dgii/endpoint_readiness.py`
- `ecf/management/commands/dgii_endpoint_plan.py`
- `ecf/urls.py`
- `ecf/views/__init__.py`
- `ecf/views/dgii_public_endpoints.py`
- `tests/test_dgii_endpoint_plan.py`

### Updated
- `etaxflow/settings.py` — `ETAXFLOW_*` placeholders (disabled by default)
- `etaxflow/urls.py` — include `ecf.urls`
- `ecf/management/commands/dgii_readiness_report.py` — Phase 025 endpoint blockers + `endpoint_plan`
- `tests/test_dgii_readiness_report.py`
- `README.md`
- `docs/dgii/PRE_CERTIFICATION_READINESS_CHECKLIST.md`
- `docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md`

## Migrations

**No changes detected**

## Endpoint metadata (defaults)

| Field | Value |
|---|---|
| software_type | `PROPIO` |
| software_name | `eTaxFlow` |
| software_version | `0.1.0` |
| public_base_url | *(blank)* |
| endpoints_enabled | `false` |
| readiness_status | `BLOCKED` |

## Planned URLs (when base URL configured)

Example host: `https://etaxflow.bcctechnologies.com.do`

- Recepción: `/fe/recepcion/api/ecf`
- Aprobación Comercial: `/fe/aprobacioncomercial/api/ecf`
- Autenticación template: `/fe/autenticacion/api/[semilla]validacioncertificado`

## Route stubs

**Added** — disabled by default (`ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false`):

- `/fe/recepcion/api/ecf`
- `/fe/aprobacioncomercial/api/ecf`
- `/fe/autenticacion/api/semilla`
- `/fe/autenticacion/api/validacioncertificado`

Return 503 JSON `{status: DISABLED, compliance_status: NOT_DGII_COMPLIANT, dgii_submission_allowed: false}`.

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `blocker_count`: **27** (includes Phase 025 endpoint blockers)

## Final pytest result

**215 passed**

## Remaining blockers (human / deploy)

- Configure and verify `ETAXFLOW_PUBLIC_BASE_URL` on approved pre-cert/staging host
- DNS + HTTPS + internet accessibility verification
- Usuario Administrador, certificate owner, authorized eNCF ranges (Phase 024 gate)
- Production signing architecture approval
- Do not submit DGII postulation until go/no-go gates pass

## Exact next recommended phase

**Phase 026 — Staging DNS/SSL deployment checklist** (deploy and verify pre-cert host; still no DGII submission).
