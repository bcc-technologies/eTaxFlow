# Pre-Certification Endpoint Design

**Phase:** 025  
**Status:** DESIGN_ONLY — not deployed, not verified, not DGII-compliant  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`

## 1. Purpose

This document defines the **planned** public HTTPS endpoints that BCC would register in the DGII portal for software postulation (URL Recepción, URL Aprobación Comercial, URL Autenticación). It is a design artifact only:

- No live DGII integration
- No production compliance claim
- No certification evidence
- URLs must not be submitted to DGII until DNS, SSL, routing, auth, signing, roles, and readiness gates are human-approved (see Phase 024 authorization gate)

Source context: `Descripcion_Tecnica_Servicios_DGII.pdf`, `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf`, proceso de certificación PDFs, Phase 024 source intake summary.

## 2. Software registration fields (planned)

| Field | Planned value | Status |
|---|---|---|
| Tipo de software | `PROPIO` | Design default in `ETAXFLOW_SOFTWARE_TYPE` |
| Nombre del software | `eTaxFlow` | Design default in `ETAXFLOW_SOFTWARE_NAME` |
| Versión del software | `0.1.0` | Design default in `ETAXFLOW_SOFTWARE_VERSION` |
| Planned public host | `etaxflow.bcctechnologies.com.do` | **TBD** until DNS/SSL/deploy approved |
| `ETAXFLOW_PUBLIC_BASE_URL` | *(empty in repo)* | Must be set only when staging/pre-cert host is approved |

Inspect live metadata:

```bash
.venv/bin/python manage.py dgii_endpoint_plan
.venv/bin/python manage.py dgii_endpoint_plan --json
```

## 3. Planned URLs (portal values — design only)

When `ETAXFLOW_PUBLIC_BASE_URL` is configured to `https://etaxflow.bcctechnologies.com.do` (example), composed values become:

| Portal field | Planned URL |
|---|---|
| URL Recepción | `https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf` |
| URL Aprobación Comercial | `https://etaxflow.bcctechnologies.com.do/fe/aprobacioncomercial/api/ecf` |
| URL Autenticación | `https://etaxflow.bcctechnologies.com.do/fe/autenticacion/api/[semilla]validacioncertificado` |

Path constants (repo):

- `ETAXFLOW_DGII_RECEPCION_PATH` = `/fe/recepcion/api/ecf`
- `ETAXFLOW_DGII_APROBACION_COMERCIAL_PATH` = `/fe/aprobacioncomercial/api/ecf`
- `ETAXFLOW_DGII_AUTENTICACION_PATH_TEMPLATE` = `/fe/autenticacion/api/[semilla]validacioncertificado`

DGII portal note: the authentication field is a **template** covering semilla and validacioncertificado sub-services under the same base path prefix. Route stubs in eTaxFlow expose separate paths `/fe/autenticacion/api/semilla` and `/fe/autenticacion/api/validacioncertificado` for staging hardening; the composed portal template remains the design registration value.

**Do not submit these URLs to DGII until deployed and verified.**

## 4. Environment separation

| Environment | Purpose | eTaxFlow status today |
|---|---|---|
| local | Developer workstation / SQLite | Active (mock/offline only) |
| staging | Internal integration lab | Not deployed |
| pre-certification | DGII pre-cert test set | Not deployed — **target for first public URLs** |
| certification | DGII certification test set | Not deployed |
| production | Live taxpayer operations | Not deployed |

Rules:

- Do **not** mix pre-certification and production hostnames or certificates.
- Do **not** point pre-cert portal URLs at production infrastructure.
- Only local/mock behavior exists in the repository today.

## 5. Endpoint ownership matrix

| URL / service | Purpose | Expected caller | Method (source-backed) | Payload (source-backed) | Repo status | Blocker | Implementation owner | Security owner |
|---|---|---|---|---|---|---|---|---|
| Recepción `/fe/recepcion/api/ecf` | Receive e-CF from counterparties / DGII test harness | External emitter or DGII test client | POST XML (emitter services doc) | e-CF XML | DESIGN_ONLY stub returns 503 when disabled | Not implemented; SSL not verified; endpoints disabled | TBD | TBD |
| Aprobación Comercial `/fe/aprobacioncomercial/api/ecf` | Commercial approval (ACECF) | Buyer / authorized approver | POST XML (formato ACECF) | ACECF signed XML | DESIGN_ONLY stub returns 503 when disabled | Not implemented; production signing not approved | TBD | TBD |
| Autenticación `/fe/autenticacion/api/semilla` | Seed for auth handshake | DGII / client per servicios DGII | GET/POST per technical doc | Semilla XML | DESIGN_ONLY stub returns 503 when disabled | Not implemented; not live | TBD | TBD |
| Autenticación `/fe/autenticacion/api/validacioncertificado` | Certificate validation step | DGII / client | POST per technical doc | Certificate/signature payload | DESIGN_ONLY stub returns 503 when disabled | Not implemented; no certs in repo | TBD | TBD |

## 6. Security baseline

- **HTTPS required** for any public DGII-facing host (traditional ports, internet-accessible, no blocked/proxy-avoidance domains per emitter technical description).
- **No private keys, passphrases, or certificates** in the repository or committed settings.
- **Logs** must redact tokens, certificate material, and signature blobs when implemented.
- **Request size limits** to be defined at implementation (Phase 027+).
- **Audit events** for any future accepted/rejected receiver traffic.
- **Allowlist / rate limiting** — decision pending security review.
- **Staging isolated from production** — separate host, certs, DB, secrets.
- **Default:** `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=False` — route stubs return safe 503 JSON, not live processing.

Disabled stub response shape (Phase 026 hardened):

```json
{
  "status": "DISABLED",
  "compliance_status": "NOT_DGII_COMPLIANT",
  "dgii_submission_allowed": false,
  "track_id": null,
  "message": "Public DGII-facing endpoints are disabled in this environment."
}
```

POST/GET to disabled routes returns **503** with the JSON above — no XML parse, no TrackId, no database writes, no live transport.

## 7. Go / no-go gate (before DGII postulation)

Do **not** fill or submit the DGII software postulation form until **all** are approved:

- [ ] Public host DNS and TLS certificate provisioned
- [ ] `ETAXFLOW_PUBLIC_BASE_URL` set to approved pre-cert/staging host (not production)
- [ ] Routes reachable from internet on HTTPS (verified externally)
- [ ] Usuario Administrador e-CF assigned (Phase 024 gate)
- [ ] Firmante / certificate owner / representative confirmed
- [ ] Production signing architecture approved (separate from test sandbox)
- [ ] Authorized eNCF ranges (Alta NCF) confirmed
- [ ] Readiness report reviewed — still expect `BLOCKED` until implementation phases complete
- [ ] Phase 024 authorization gate signed off

## Related artifacts

- `docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md`
- `docs/dgii/PRE_CERTIFICATION_READINESS_CHECKLIST.md`
- `docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md` — Phase 026 staging DNS/SSL checklist (manual verification only)
- `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md` — Phase 027 receiver contract (internal design only)
- `.env.staging.example` — staging env placeholders (no real secrets)
- `ecf/dgii/receiver.py` — internal classification skeleton
- `ecf/dgii/endpoints.py` — URL composition helper
- `ecf/management/commands/dgii_endpoint_plan.py` — read-only plan command
- `ecf/management/commands/dgii_receiver_contract.py` — receiver support matrix

## Next phase

**Phase 028 — Non-production inbound XML lab** — controlled synthetic XML testing internally, no public network, no DGII.
