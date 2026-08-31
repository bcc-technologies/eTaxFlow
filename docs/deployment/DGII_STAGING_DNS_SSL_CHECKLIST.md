# DGII Staging / Pre-Certification DNS & SSL Checklist

**Phase:** 026  
**Status:** CHECKLIST_ONLY — not deployed, not verified, not DGII-compliant  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`

## 1. Purpose

Prepare **staging/pre-certification** public exposure for eTaxFlow DGII-facing receiver/auth route stubs defined in Phase 025. This document is a human-operated checklist only:

- No live DGII calls
- No production signing
- No compliance or certification claim
- No automatic deployment from this repository
- Route stubs remain **disabled** (`ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false`) until explicit human approval

Source requirements (emitter/receiver services): SSL, internet-accessible, traditional HTTPS ports, domain not blocked / no proxy-avoidance — see `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf`.

Environment separation: **Pre-Certificación**, **Certificación**, and **Producción** must not share hostnames, certificates, secrets, or databases.

Related artifacts:

- `docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md`
- `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md` (Phase 027 — internal receiver contract; routes remain disabled)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md` (Phase 028 — synthetic inbound XML lab; not certification evidence)
- `.env.staging.example`
- `python manage.py dgii_endpoint_plan`
- `python manage.py dgii_receiver_contract`
- `python manage.py dgii_inbound_xml_lab` (Phase 028 — synthetic fixtures only)
- `docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md` (Phase 036 — offline evidence collector; no network checks)
- `python manage.py dgii_staging_evidence_lab` (Phase 036 — template/validate/report only)

## 2. Planned host

| Item | Value | Status |
|---|---|---|
| Planned host | `etaxflow.bcctechnologies.com.do` | **TBD** |
| Owner | _TBD_ | |
| DNS provider | _TBD_ | |
| Hosting provider | _TBD_ | |
| Environment | staging / pre-certification only | Not production |

Do **not** point this host at production infrastructure or reuse production TLS material.

## 3. Required DNS steps

- [ ] Choose subdomain (`etaxflow.bcctechnologies.com.do` or approved alternative)
- [ ] Create **A** or **CNAME** record to staging/pre-cert target (document target IP/hostname)
- [ ] Record TTL and change ticket reference
- [ ] Verify propagation manually (`dig` — see section 8)
- [ ] Confirm record does **not** alias production load balancers
- [ ] Confirm no shared DNS with production e-CF endpoints
- [ ] Document rollback: remove or repoint record if staging is decommissioned

## 4. Required TLS/SSL steps

- [ ] Obtain valid certificate for planned host (Let's Encrypt, commercial CA, or org PKI — human choice)
- [ ] **HTTPS only** — terminate TLS at approved edge (load balancer / reverse proxy)
- [ ] Redirect HTTP → HTTPS
- [ ] Document certificate owner and renewal procedure (auto-renew + alert)
- [ ] Private key stored in approved secret manager / HSM — **never in git**
- [ ] Certificate **not** committed to repository
- [ ] Staging certificate distinct from production certificate
- [ ] Confirm cipher/TLS version policy with security owner

## 5. Network / access requirements

Per DGII emitter technical description (checklist — verify against local PDF):

- [ ] Host is **internet accessible** from DGII test harness perspective
- [ ] **Traditional HTTPS port** (443) exposed; document any non-standard ports (avoid if possible)
- [ ] Domain not on blocklists; no proxy-avoidance patterns
- [ ] Firewall / security group allows inbound 443 from internet (minimal scope)
- [ ] Outbound rules documented if app must call external services later (not in Phase 026)
- [ ] Rate limiting decision: _TBD_
- [ ] Request body size limit: _TBD_ (document before enabling endpoints)
- [ ] Request timeout policy: _TBD_
- [ ] Logging redaction for tokens, certs, signatures: _required before live processing_

## 6. Application settings

Configure via environment / secret manager — **placeholders in** `.env.staging.example` **only**.

| Variable | Purpose | Phase 026 default |
|---|---|---|
| `ETAXFLOW_PUBLIC_BASE_URL` | Composed portal URL base | blank |
| `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS` | Enable route processing | `false` |
| `ALLOWED_HOSTS` | Django host header allowlist | planned host + localhost |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origin trust | planned host URL |
| `SECURE_SSL_REDIRECT` | Force HTTPS | `true` when TLS live |
| `SESSION_COOKIE_SECURE` | Secure cookies | `true` when TLS live |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie | `true` when TLS live |
| `SECURE_HSTS_SECONDS` | HSTS | `0` on staging until security approves |
| `DATABASE_URL` | Staging DB | placeholder |
| `SECRET_KEY` | Django secret | placeholder — secret manager |
| `SIGNING_*` | Production signing | **disabled** |
| `DGII_LIVE_TRANSPORT_ENABLED` | Outbound DGII HTTP | **false** |

Signing and production certificates remain **out of scope** for Phase 026.

## 7. Endpoint verification checklist

While `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false`, each route must respond with **503** and safe JSON:

| Route | Expected status | Expected JSON fields |
|---|---|---|
| `/fe/recepcion/api/ecf` | 503 | `status=DISABLED`, `compliance_status=NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, `track_id=null` |
| `/fe/aprobacioncomercial/api/ecf` | 503 | same |
| `/fe/autenticacion/api/semilla` | 503 | same |
| `/fe/autenticacion/api/validacioncertificado` | 503 | same |

Verification rules:

- [ ] GET and POST both return 503 (no XML processing)
- [ ] No `TrackId` created
- [ ] No `Invoice` / `Document` / `ECFDocument` mutation
- [ ] No stack traces in response body
- [ ] Message indicates endpoints disabled in environment

Local test (after deploy, manual):

```bash
curl -sS -o /tmp/recepcion.json -w "%{http_code}" \
  -X POST https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf \
  -H "Content-Type: application/xml" --data-binary @/dev/null
# Expect: 503 and DISABLED JSON
```

## 8. External verification commands (MANUAL_LATER)

**Do not run automatically from CI in Phase 026.** Human executes after DNS/SSL deploy:

```bash
# DNS propagation
dig +short etaxflow.bcctechnologies.com.do A
dig +short etaxflow.bcctechnologies.com.do CNAME

# HTTP headers / redirect
curl -I http://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf
curl -I https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf

# TLS certificate inspect
openssl s_client -connect etaxflow.bcctechnologies.com.do:443 -servername etaxflow.bcctechnologies.com.do </dev/null

# Disabled stub check (POST body ignored)
curl -sS -X POST https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf \
  -H "Content-Type: application/xml" --data-binary '<ECF/>'
```

Mark each command result in the deployment ticket when executed.

## 9. Go / no-go table

| Gate | Status | Owner | Date | Notes |
|---|---|---|---|---|
| DNS verified | BLOCKED | _TBD_ | | |
| TLS verified | BLOCKED | _TBD_ | | |
| External reachability verified | BLOCKED | _TBD_ | | |
| Route stubs verified disabled (503) | OPEN (local) | Engineering | | Repo default |
| Security owner approves exposure | BLOCKED | _TBD_ | | |
| Tax/compliance owner approves | BLOCKED | _TBD_ | | |
| Staging owner approves | BLOCKED | _TBD_ | | |
| Readiness remains BLOCKED | YES | — | | Expected until later phases |
| Submit URLs to DGII portal | **NO-GO** | — | | |

## 10. Next phase

**Phase 027 — Pre-certification receiver endpoint implementation plan** (internal contract + tests for ARECF/ACECF/ECF received — still no DGII live).

## Phase 036 evidence collector

Use `dgii_staging_evidence_lab` for **offline/manual** evidence templates and validation under `runtime/dgii_staging_evidence/`.

- Does **not** perform DNS/TLS/HTTPS/network checks
- Does **not** enable public endpoints
- Does **not** call DGII or create TrackId
- Does **not** claim staging approval or certification evidence
- Default decision: `STAGING_EVIDENCE_BLOCKED`
