# DGII e-CF Document Inventory

**Purpose:** Track official DGII source documents required before any claim of e-CF XML compliance or production submission.

**Rules:**
- Do not invent PDF/XSD contents.
- `source_status=LOCAL_COPY_AVAILABLE` only when the file exists under `docs/dgii/sources/`.
- Official portal hub: [Documentación sobre e-CF (DGII)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx)
- Review status: `collected` / `reviewed` / `mapped` — Phase 024 marks `collected` only unless explicitly reviewed for implementation.
- Impact flags: `code`, `certification`, `signing`, `services`, `printed`, `acuse`, `aprobacion`, `contingency`, `governance` (comma-separated where applicable).

**Boundary:** Collected sources enable catalog scaffolding and human readiness gates. They do **not** authorize production e-CF XML, signing, authentication, or DGII submission. Status remains **`NOT_DGII_COMPLIANT`**.

## Phase 024 priority documents

| filename | title | version/date shown | category | phase relevance | source_status | impact | review status | notes |
|---|---|---|---|---|---|---|---|---|
| `Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | Formato Comprobante Fiscal Electrónico (e-CF) | v1.0 \| Octubre 2025 (bitácora 09-10-2025) | formato | 005–024 catalog / obligation matrix | LOCAL_COPY_AVAILABLE | code, certification, signing, governance | collected | Mandatory digital signature on every e-CF; field obligations for Tipo 31+ |
| `Formato_Aprobacion_Comercial_v1.0.pdf` | Formato Aprobación Comercial (ACECF) | v1.0, Enero 2020 | formato | 024+ commercial ack | LOCAL_COPY_AVAILABLE | code, services, aprobacion, signing | collected | Requires signed commercial approval XML; not production-ready in eTaxFlow |
| `Formato_Acuse_de_Recibo_v1.0.pdf` | Formato Acuse de Recibo (ARECF) | v1.0 | formato | 024+ receipt ack | LOCAL_COPY_AVAILABLE | code, services, acuse, signing | collected | Requires signed receipt-ack detail; not production-ready in eTaxFlow |
| `Proceso_Certificacion_Emisor_Electronico.pdf` | Proceso de Certificación para ser Emisor Electrónico | not extracted (references Ley 32-23, Decreto 587-24, Norma 01-2020) | proceso | 024 certification gate | LOCAL_COPY_AVAILABLE | certification, governance | collected | Formal process: Solicitud → Set de Pruebas → Certificación |
| `Proceso_Certificacion_EmisorElectronico_Proveedor_Servicios_FECertificado.pdf` | Proceso de Certificación Emisor + Proveedor FE Certificado | not extracted | proceso | 024 route decision | LOCAL_COPY_AVAILABLE | certification, governance | collected | Alternate route when using certified FE provider |
| `Solicitud_Usuario_Administrador_de_e-CF.pdf` | Solicitud Usuario Administrador de e-CF | Mayo 2026 | instructivo | 024 governance | LOCAL_COPY_AVAILABLE | governance, certification | collected | Admin user must be assigned **before** authorization request; RNC/OFV/cert upkeep |
| `Instructivo_App_Firma_Digital.pdf` | Instructivo App Firma Digital | v1.0, Enero 2020 | instructivo | signing ops | LOCAL_COPY_AVAILABLE | signing, governance | collected | Operational signing app guidance; not implemented in eTaxFlow |
| `Firmado_de_e-CF.pdf` | Firmado Comprobantes Fiscales Electrónicos (e-CF) | not extracted | firma | 016–024 signing design | LOCAL_COPY_AVAILABLE | signing, code, certification | collected | SHA-256, enveloping signature, `Reference URI=""`, X509 in KeyInfo |
| `Instructivo_Delegaciones_Roles_Facturacion_Electronica.pdf` | Instructivo Delegaciones de Roles de Facturación Electrónica | v2.0, Junio 2025 | instructivo | 024 governance | LOCAL_COPY_AVAILABLE | governance, certification | collected | Role delegation (Solicitante, Firmante, Aprobador, etc.) |
| `Instructivo_Facturador_Gratuito_de_FE.pdf` | Instructivo Facturador Gratuito de FE | v2.0, Julio 2026 | instructivo | ops reference | LOCAL_COPY_AVAILABLE | governance | collected | DGII free facturador reference; eTaxFlow is separate software path |
| `Instructivo_Contingencia_FE.pdf` | Instructivo Contingencia FE | not extracted | instructivo | contingency | LOCAL_COPY_AVAILABLE | contingency, governance, certification | collected | Contingency entry/exit/registration; workflow not implemented |
| `Descripcion_Tecnica_Servicios_DGII.pdf` | Descripción Técnica Servicios DGII | not extracted (has bitácora) | servicios | 006+ DGII services | LOCAL_COPY_AVAILABLE | services, certification, code | collected | Auth/semilla/token, recepción, TrackId, environments |
| `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf` | Descripción Técnica Servicios Emisores Electrónicos | not extracted (has bitácora) | servicios | 006+ emitter services | LOCAL_COPY_AVAILABLE | services, code, signing | collected | XML naming, content restrictions, emitter-side signing rules |
| `Informe_Tecnico_e-CF_v1.0.pdf` | Informe Técnico Comprobante Fiscal Electrónico | v1.0 | servicios | 005–024 context | LOCAL_COPY_AVAILABLE | printed, contingency, governance | collected | Schema concepts, contingency overview, printed representation context |
| `Representacion_Impresa_e-CF.pdf` | Modelos Ilustrativos Representación Impresa (RI) | not extracted | printed | 018+ print layer | LOCAL_COPY_AVAILABLE | printed, governance | collected | Illustrative printed models; local PDF draft is NON_PRODUCTION |

## Additional collected formatos and XSDs

| filename | title | version/date shown | category | phase relevance | source_status | impact | review status | notes |
|---|---|---|---|---|---|---|---|---|
| `Formato_Anulacion_de_e-NCF_v1.0.pdf` | Formato Anulación de e-NCF (ANECF) | v1.0 (bitácora 24-05-2022) | formato | later annulment | LOCAL_COPY_AVAILABLE | code | collected | ANECF XSD also present locally |
| `Formato_Resumen_Factura_Consumo_Electronica_v1.0.pdf` | Formato Resumen Factura Consumo Electrónica (RFCE) | not extracted | formato | RFCE 32 | LOCAL_COPY_AVAILABLE | code, services | collected | RFCE XSD also present locally |
| `e-CF_31_v1.0.xsd` | XSD e-CF 31 | v1.0 | xsd | 005–014 validation | LOCAL_COPY_AVAILABLE | code | collected | Wired into local unsigned validation; experimental stub for type-name defect |
| `e-CF_32_v1.0.xsd` … `e-CF_47_v1.0.xsd` | XSD TipoeCF 32–47 | v1.0 | xsd | future types | LOCAL_COPY_AVAILABLE | code | collected | Local schema store only; not wired beyond Tipo 31 |
| `ACECF_v1.0.xsd` | XSD Aprobación Comercial | v1.0 | xsd | commercial ack | LOCAL_COPY_AVAILABLE | code, aprobacion | collected | |
| `ARECF_v1.0.xsd` | XSD Acuse de Recibo | v1.0 | xsd | receipt ack | LOCAL_COPY_AVAILABLE | code, acuse | collected | |
| `ANECF_v1.0.xsd` | XSD Anulación e-NCF | v1.0 | xsd | annulment | LOCAL_COPY_AVAILABLE | code | collected | |
| `RFCE_32_v1.0.xsd` | XSD RFCE 32 | v1.0 | xsd | RFCE | LOCAL_COPY_AVAILABLE | code, services | collected | |
| `Semilla_v1.0.xsd` | XSD Semilla | v1.0 | xsd | auth | LOCAL_COPY_AVAILABLE | services, code | collected | Mock auth only in repo today |

## Missing legal / priority sources

| filename | title | version/date shown | category | phase relevance | source_status | impact | review status | notes |
|---|---|---|---|---|---|---|---|---|
| `Norma_General_01-2020.pdf` | Norma General 01-2020 | — | legal | legal baseline | MISSING | governance, certification | missing | Referenced by certification process; collect from DGII/Gaceta |
| `Ley_32-23.pdf` | Ley 32-23 | — | legal | legal baseline | MISSING | governance, certification | missing | Electronic invoicing law |
| `Decreto_587-24.pdf` | Decreto 587-24 | — | legal | legal baseline | MISSING | governance, certification | missing | Implementing decree |

## Software registration fields (from certification/solicitud sources — human confirmation required)

These are **not files** but mandatory readiness items extracted from proceso/solicitud documents:

| requirement | source-backed | eTaxFlow status |
|---|---|---|
| RNC registered | Proceso Certificación | PARTIAL (local demo RNC only) |
| OFV access | Proceso / Usuario Administrador | MANUAL_REQUIRED |
| Alta NCF / authorized eNCF ranges | Proceso Certificación | MANUAL_REQUIRED (demo ranges only locally) |
| Usuario Administrador e-CF before authorization | Solicitud Usuario Administrador | NOT CONFIRMED |
| Certificado digital procedimiento tributario | Proceso / Usuario Administrador | NOT CONFIGURED |
| Software name / version / type | Solicitud / Proceso | READY (local metadata only) |
| URL Recepción | Solicitud / Servicios DGII | BLOCKED (blank) |
| URL Aprobación Comercial | Solicitud / Servicios DGII | BLOCKED (blank) |
| URL Autenticación | Solicitud / Servicios DGII | BLOCKED (blank) |

## Local collection convention

Store official binaries under `docs/dgii/sources/` (gitignored except README + `.gitkeep`). See `docs/dgii/sources/README.md`.

Never store official PDFs/XSDs under `ecf/dgii/` (Python package / code only).

Phase 024 artifacts:
- `docs/dgii/source_intake/PHASE_024_SOURCE_REVIEW_SUMMARY.md`
- `docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md`
