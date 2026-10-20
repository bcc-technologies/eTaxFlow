# Phase 024 — Source Review Summary

**Date:** 2026-08-17  
**Status:** Source intake complete for Phase 024 priority set; human authorization gate open  
**Compliance boundary:** `NOT_DGII_COMPLIANT` — not certification evidence

## Documents received (local copy available)

Phase 024 priority PDFs under `docs/dgii/sources/`:

| Document | Local filename |
|---|---|
| Formato Aprobación Comercial v1.0 | `Formato_Aprobacion_Comercial_v1.0.pdf` |
| Formato Acuse de Recibo v1.0 | `Formato_Acuse_de_Recibo_v1.0.pdf` |
| Formato Comprobante Fiscal Electrónico (e-CF) V1.0 | `Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` |
| Proceso de Certificación Emisor Electrónico | `Proceso_Certificacion_Emisor_Electronico.pdf` |
| Proceso Certificación Emisor + Proveedor FE Certificado | `Proceso_Certificacion_EmisorElectronico_Proveedor_Servicios_FECertificado.pdf` |
| Instructivo Facturador Gratuito FE | `Instructivo_Facturador_Gratuito_de_FE.pdf` |
| Instructivo Contingencia FE | `Instructivo_Contingencia_FE.pdf` |
| Solicitud Usuario Administrador de e-CF | `Solicitud_Usuario_Administrador_de_e-CF.pdf` |
| Instructivo App Firma Digital | `Instructivo_App_Firma_Digital.pdf` |
| Firmado de e-CF | `Firmado_de_e-CF.pdf` |
| Instructivo Delegaciones de Roles FE | `Instructivo_Delegaciones_Roles_Facturacion_Electronica.pdf` |
| Descripción Técnica Servicios DGII | `Descripcion_Tecnica_Servicios_DGII.pdf` |
| Descripción Técnica Emisores Electrónicos | `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf` |
| Representación Impresa (modelos ilustrativos) | `Representacion_Impresa_e-CF.pdf` |
| Informe Técnico e-CF v1.0 | `Informe_Tecnico_e-CF_v1.0.pdf` |

Additional local XSD/formato store (not Phase 024 minimum but collected): TipoeCF 32–47 XSDs, ACECF/ARECF/ANECF/RFCE/Semilla XSDs, ANECF/RFCE PDFs.

**Total local source files:** 32 under `docs/dgii/sources/` (excluding README/.gitkeep).

## Documents still missing

| Document | Expected filename | Impact |
|---|---|---|
| Norma General 01-2020 | `Norma_General_01-2020.pdf` | Legal baseline referenced by certification process |
| Ley 32-23 | `Ley_32-23.pdf` | Electronic invoicing law |
| Decreto 587-24 | `Decreto_587-24.pdf` | Implementing decree |

Official certification **test-set fixtures** are not present and must not be invented.

## Major requirements extracted (source-backed)

### 1. Formal DGII certification process (three blocks)

From proceso de certificación documents:

1. **Solicitud** — registration/postulation with taxpayer and software data
2. **Set de Pruebas** — official test execution (not started in eTaxFlow)
3. **Certificación** — DGII authorization after successful tests

Prerequisites cited across proceso/solicitud sources:

- RNC
- OFV access
- Alta NCF / authorized e-NCF ranges
- Certificado digital para procedimiento tributario
- Software e-CF and cumplimiento tributario
- Usuario Administrador de e-CF **before** authorization request

### 2. Software registration metadata

Solicitud/proceso sources require, among others:

- Tipo de software
- Nombre del software
- Versión
- **URL Recepción**
- **URL Aprobación Comercial**
- **URL Autenticación**

eTaxFlow has local software metadata only; all three URLs remain blank/un deployed.

### 3. Governance roles (human assignment)

From Usuario Administrador + Delegaciones instructivos:

- Usuario Administrador e-CF (maintain RNC, OFV credentials, certificado tributario, authorized signatories)
- Solicitante, Firmante, Aprobador Comercial (role delegation model)
- Representative linked to RNC

No owner names are recorded in the repo — see authorization gate doc.

### 4. Signing is mandatory (not optional)

From Formato e-CF + Firmado de e-CF + Descripción Técnica Emisores:

- Every e-CF must contain digital signature
- SHA-256 digest
- Enveloping signature
- `Reference URI=""`
- X509 certificate in `KeyInfo`

eTaxFlow today: unsigned draft + test-only sandbox + signing placeholder — **not production signing**.

### 5. Services architecture

From Descripción Técnica Servicios DGII + Emisores Electrónicos:

- DGII services vs emitter/receiver services are separate
- Master formats include `ECF`, `ACECF`, `ARECF`
- Environments: Pre-Certificación, Certificación, Producción
- Receiver services must be SSL and internet-accessible (when live)
- XML file naming standards and content restrictions apply
- Empty tags not permitted (emitter-side rules)

Repo status: mocked contracts only; no live transport.

### 6. Acuse and Aprobación Comercial

From Formato ARECF + ACECF:

- Both require structured detail **and** digital signature
- Cannot be treated as production until real signing + live endpoints exist

### 7. Contingency and printed representation

- Contingency instructivo defines entry/exit/registration — workflow NOT IMPLEMENTED
- Representación impresa provides illustrative models — local PDF is NON_PRODUCTION_DRAFT

## Code-impact vs human-decision-impact

| Area | Code impact (future phases) | Human decision impact (Phase 024 gate) |
|---|---|---|
| Tipo 31 field catalog / unsigned XSD lab | Partial scaffolding exists | Review Formato e-CF v1.0 Oct 2025 obligations authoritatively |
| XMLDSig production signer | Architecture docs + test sandbox only | Approve custody model, certificate owner, HSM/KMS vs app signer |
| DGII auth/reception/status | Mock contracts | Deploy URLs, SSL, staging owner, environment choice |
| Acuse / Aprobación endpoints | Not implemented | Decide if BCC hosts receiver services vs provider |
| Certification route | Harness scaffold only | **Internal software vs certified FE provider** |
| Usuario Administrador / roles | Not in app | Assign named humans before any DGII solicitud |
| Authorized eNCF ranges | Demo/local only | Confirm Alta NCF with DGII |
| Contingency | Not implemented | Approve business/ops policy |
| Legal PDFs missing | Inventory blocker | Collect Norma/Ley/Decreto PDFs |

## No-compliance boundary (explicit)

- Local PDF/XSD presence ≠ DGII authorization
- Mock services ≠ live recepción
- Test-only XMLDSig sandbox ≠ production signing
- Unsigned draft validation ≠ certification evidence
- `dgii_readiness_report` remains **BLOCKED** / **NOT_DGII_COMPLIANT**
- **No live DGII calls, TrackId creation, or production XML submission in Phase 024**

## Next recommended phase

**Phase 025 — Pre-certification endpoint design** (design-only URLs for Recepción / Aprobación Comercial / Autenticación; still no live calls).
