# DGII e-CF Document Inventory

**Purpose:** Track official DGII source documents required before any claim of e-CF XML compliance or production submission.

**Rules:**
- Do not invent PDF/XSD contents.
- `local_file_present` is `yes` only when the file exists under `docs/dgii/sources/`.
- Official portal hub: [Documentación sobre e-CF (DGII)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx)
- Status meanings: `missing` / `collected` / `reviewed` / `mapped`
- Do **not** mark `reviewed` or `mapped` unless the file was actually inspected for implementation use.

| document_name | source_url_or_manual_location | local_file_present | local_path | required_for_phase | implementation_area | status | notes |
|---|---|---|---|---|---|---|---|
| Informe Técnico e-CF v1.0 | https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx (Informe y Descripción Técnica) | yes | docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf | 005 / 006+ | schema concepts, contingency, printed representation overview | collected | Downloaded 2026-08-09; not fully reviewed for field obligations |
| Descripción Técnica Servicios DGII | same hub (Informe y Descripción Técnica) | yes | docs/dgii/sources/Descripcion_Tecnica_Servicios_DGII.pdf | 006+ services | auth/semilla/token, recepción, consulta TrackId, RFCE | collected | Downloaded 2026-08-09; service implementation not started |
| Descripción Técnica Servicios Emisores Electrónicos | same hub (Informe y Descripción Técnica) | no | | 006+ emitter services | emitter-side service contracts | missing | Automatic download failed (404 on guessed paths); download manually from portal |
| Formato Comprobante Fiscal Electrónico (e-CF) V 1.0 | same hub (Formatos XML) | yes | docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | 005 catalog / 006 XML | XML field catalog + obligation matrix | collected | Downloaded 2026-08-09; field-by-field review still pending |
| Formato Acuse de Recibo v1.0 | same hub (Formatos XML) | no | | later receipt ack | ARECF | missing | Automatic download failed; download manually from portal |
| Formato Aprobación Comercial V1.0 | same hub (Formatos XML) | yes | docs/dgii/sources/Formato_Aprobacion_Comercial_v1.0.pdf | later commercial ack | ACECF | collected | Downloaded 2026-08-09; out of current Tipo 31 draft scope |
| Representación Impresa e-CF | same hub (Informe y Descripción Técnica) | yes | docs/dgii/sources/Representacion_Impresa_e-CF.pdf | later print layer | printed representation models | collected | Downloaded 2026-08-09; illustrative models |
| XSD e-CF 31 v1.0 | same hub (Documentación Técnica XSD) | yes | docs/dgii/sources/e-CF_31_v1.0.xsd | 005 catalog / 006 validation | TipoeCF 31 structure | collected | Downloaded 2026-08-09; element names inspected for skeleton catalog only |
| Norma General 01-2020 | DGII legal library / Gaceta Oficial | no | | legal baseline | regulatory framework | missing | Not found via automatic URL guesses; collect authoritative PDF manually |
| Ley 32-23 | DGII legal library / Gaceta Oficial | no | | legal baseline | electronic invoicing law | missing | Not found via automatic URL guesses; collect authoritative PDF manually |
| Decreto 587-24 | DGII legal library / Gaceta Oficial | no | | legal baseline | implementing decree | missing | Not found via automatic URL guesses; collect authoritative PDF manually |
| Autenticación / semilla / token | Covered in Descripción Técnica Servicios DGII | yes (parent doc) | docs/dgii/sources/Descripcion_Tecnica_Servicios_DGII.pdf | 007+ auth | seed/token | collected | Covered by Servicios DGII PDF; dedicated auth implementation not started |
| Certificación / set de pruebas | same e-CF hub (Proceso de Certificación FE) | no | | certification | official test packs | missing | Do not invent certification fixtures |
| Contingencia | Covered in Informe Técnico e-CF | yes (parent doc) | docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf | later contingency | offline emission / regularization | collected | Covered by Informe Técnico; contingency workflow not implemented |

## Local collection convention

Store official binaries under `docs/dgii/sources/` (gitignored except README + `.gitkeep`). See `docs/dgii/sources/README.md`.

## Phase interpretation

Collected sources enable **catalog scaffolding**. They do **not** authorize production e-CF XML, signing, authentication, or DGII submission.
