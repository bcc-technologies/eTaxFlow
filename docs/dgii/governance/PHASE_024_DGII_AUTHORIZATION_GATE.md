# Phase 024 — DGII Authorization Gate

**Status:** `HUMAN_DECISION_GATE`  
**Effective:** 2026-08-17  
**Repo compliance boundary:** `NOT_DGII_COMPLIANT`  
**Submission:** `dgii_submission_allowed=false`

This document records **human decisions required** before any DGII pre-certification activity. It does not authorize live integration.

## Explicit prohibitions (remain in force)

- No live DGII API calls from eTaxFlow
- No TrackId creation or polling against DGII production/pre-cert endpoints
- No production XMLDSig or private keys in the repository
- No claim of DGII compliance, certification, or approval
- No use of local XSD/PDF/mock/sandbox results as certification evidence
- No invention of official certification test cases or authorized e-NCF ranges

## Route decision (required)

BCC must choose **one primary path** before solicitud:

| Option | Description | Implications |
|---|---|---|
| A — Software interno propio | BCC develops/operates its own e-CF software (eTaxFlow) | BCC owns URLs, signing custody, certification set, ongoing compliance |
| B — Proveedor certificado | BCC uses a DGII-certified FE provider | Provider owns certified software path; BCC integrates operationally |

**Decision:** _TBD — fill by authorized management/legal/tax owner_

**Decision owner:** _TBD_  
**Decision date:** _TBD_  
**Rationale notes:** _TBD_

## Role assignments (required before solicitud)

| Role | Purpose (source-backed) | Assigned name | Assigned date | Notes |
|---|---|---|---|---|
| OFV owner | OFV enrollment, access, credential lifecycle | _TBD_ | _TBD_ | Manual checkpoint in readiness report |
| Usuario Administrador e-CF | Admin user before authorization request; maintains RNC, OFV, certificado tributario, signatory registry | _TBD_ | _TBD_ | See `Solicitud_Usuario_Administrador_de_e-CF.pdf` |
| Solicitante | Certification/postulation actor | _TBD_ | _TBD_ | Delegaciones instructivo |
| Firmante | Authorized e-CF signer | _TBD_ | _TBD_ | Must match DGII-registered signatories |
| Aprobador Comercial | Commercial approval actor (ACECF) | _TBD_ | _TBD_ | Required if BCC emits/receives commercial approvals |
| Representative linked to RNC | Legal/tax representative for RNC | _TBD_ | _TBD_ | Certificate/tax procedure linkage |
| Certificate owner | Custody of certificado digital procedimiento tributario | _TBD_ | _TBD_ | Not stored in repo |
| Staging owner | Pre-certification/staging environment operations | _TBD_ | _TBD_ | Isolated from production |
| DGII certification approver | Go/no-go for pre-certification and certification submission | _TBD_ | _TBD_ | Management + tax/legal sign-off |

## Signing custody model (required)

**Decision:** _TBD_

Document at minimum:

- Where private keys live (HSM, cloud KMS, signing appliance, manual process)
- Who can trigger production signing
- Rotation and revocation procedure
- Separation between dev/test certificates and production certificates
- Alignment with `Firmado_de_e-CF.pdf` (SHA-256, enveloping, `Reference URI=""`, X509 KeyInfo)

eTaxFlow repo policy: **no private keys committed**; production signer not approved.

## Public URLs (required for solicitud — design in Phase 025, not deployed)

| URL field | Planned value (example host) | Environment | SSL verified | Owner | Status |
|---|---|---|---|---|---|
| URL Recepción | `https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf` | Pre-Cert first | _TBD_ | _TBD_ | BLOCKED / DESIGN_ONLY |
| URL Aprobación Comercial | `https://etaxflow.bcctechnologies.com.do/fe/aprobacioncomercial/api/ecf` | Pre-Cert first | _TBD_ | _TBD_ | BLOCKED / DESIGN_ONLY |
| URL Autenticación | `https://etaxflow.bcctechnologies.com.do/fe/autenticacion/api/[semilla]validacioncertificado` | Pre-Cert first | _TBD_ | _TBD_ | BLOCKED / DESIGN_ONLY |

Phase 025 documents these in `docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md`. Inspect with `python manage.py dgii_endpoint_plan`. **Do not submit to DGII portal until DNS, HTTPS, and internet accessibility are verified.** Route stubs exist but return 503 DISABLED when `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false`.

## Pre-certification / certification go-no-go

| Gate | Status | Approver | Date |
|---|---|---|---|
| Official source inventory reviewed (Phase 024) | OPEN | _TBD_ | _TBD_ |
| Missing legal PDFs collected (Norma/Ley/Decreto) | BLOCKED | _TBD_ | _TBD_ |
| Route A vs B decided | BLOCKED | _TBD_ | _TBD_ |
| Usuario Administrador assigned | BLOCKED | _TBD_ | _TBD_ |
| Production signing architecture approved | BLOCKED | _TBD_ | _TBD_ |
| Authorized eNCF ranges confirmed (Alta NCF) | BLOCKED | _TBD_ | _TBD_ |
| Public URLs deployed (staging) | BLOCKED | _TBD_ | _TBD_ |
| Acuse/Aprobación services ready (signed, live) | BLOCKED | _TBD_ | _TBD_ |
| Contingency process approved | BLOCKED | _TBD_ | _TBD_ |
| Submit DGII pre-certification solicitud | **NO-GO** | — | — |

## Sign-off

| Function | Name | Signature/date |
|---|---|---|
| Engineering lead | _TBD_ | _TBD_ |
| Tax/compliance owner | _TBD_ | _TBD_ |
| Security owner | _TBD_ | _TBD_ |
| Executive approver | _TBD_ | _TBD_ |

Until sign-off rows are completed, eTaxFlow remains a **local laboratory MVP** only.
