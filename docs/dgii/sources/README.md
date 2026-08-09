# DGII official sources (local ignored store)

This folder holds downloaded official DGII e-CF technical documents for local development.

## Git policy

- Tracked: `README.md`, `.gitkeep`
- Ignored: PDFs, XSDs, XML, Excel, archives under this directory
- Do **not** commit government binaries unless the project later decides otherwise

## Official documentation hub

Visit:

https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx

## Expected filenames in this folder

Use these exact local names when downloading manually (or update `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md` if you rename):

| expected_local_filename | official document name on portal |
|---|---|
| `Informe_Tecnico_e-CF_v1.0.pdf` | Informe Técnico e-CF v1.0 |
| `Descripcion_Tecnica_Servicios_DGII.pdf` | Descripción Técnica Servicios DGII |
| `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf` | Descripción Técnica Servicios Emisores Electrónicos |
| `Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | Formato Comprobante Fiscal Electrónico (e-CF) V 1.0 |
| `Formato_Acuse_de_Recibo_v1.0.pdf` | Formato Acuse de Recibo v1.0 |
| `Formato_Aprobacion_Comercial_v1.0.pdf` | Formato Aprobación Comercial V1.0 |
| `Representacion_Impresa_e-CF.pdf` | Representación Impresa (Modelos ilustrativos) |
| `e-CF_31_v1.0.xsd` | e-CF 31 v.1.0 (XSD) |
| `Norma_General_01-2020.pdf` | Norma General 01-2020 |
| `Ley_32-23.pdf` | Ley 32-23 |
| `Decreto_587-24.pdf` | Decreto 587-24 |

## Manual download instructions

1. Open the official DGII e-CF documentation hub above.
2. Download each required document using the portal **Descargar** links.
3. Save into: `docs/dgii/sources/`
4. Rename to the expected local filenames in the table above.
5. Update `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`:
   - `local_file_present = yes`
   - `local_path = docs/dgii/sources/<filename>`
   - `status = collected` (only set `reviewed` / `mapped` after you inspect the file)
6. Do **not** rename files without updating the inventory.

## Legal documents

Norma General 01-2020, Ley 32-23, and Decreto 587-24 may live under DGII legal library / Gaceta Oficial pages rather than the e-CF technical hub. Locate the authoritative PDF, place it here with the expected filename, then update inventory.

## Rules

- Do not invent document contents.
- Do not invent XML field names from memory.
- Presence of a file means `collected`, not compliance.
- XSD presence does not authorize production e-CF generation.
