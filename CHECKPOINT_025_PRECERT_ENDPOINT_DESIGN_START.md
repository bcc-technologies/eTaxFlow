# Checkpoint 025 — Pre-Certification Endpoint Design Start

## Branch

`revamp/dgii-vault-mvp`

## Baseline (pre-025)

- Phase 024 commit: `59625c3`
- Tests: **207 passed**
- Readiness: `overall_status=BLOCKED`, `compliance_status=NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`
- Software metadata (legacy settings): name `eTaxFlow`, version `MVP`, type `INTERNAL`
- Blocked URL fields: `DGII_URL_RECEPCION`, `DGII_URL_APROBACION_COMERCIAL`, `DGII_URL_AUTENTICACION` (all blank)

## Intended scope

- Design-only pre-certification endpoint plan for DGII portal fields (Recepción, Aprobación Comercial, Autenticación)
- Safe settings placeholders and URL composition helper
- `dgii_endpoint_plan` command (read-only, no network)
- Extended readiness blockers for endpoint deployment
- Disabled URL route stubs (503 JSON) when `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=False`

## Explicit non-goals

- Live DGII calls, XML submission, TrackId, production signing
- Certificates/private keys in repo
- Compliance or certification-ready claims
- Deployed/verified HTTPS endpoints
- Production URL defaults enabled
