# Checkpoint 005 — DGII Source Collection and Tipo e-CF 31 Catalog

## Files changed

- `.gitignore`
- `docs/dgii/sources/README.md`
- `docs/dgii/sources/.gitkeep`
- `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `ecf/dgii/field_catalogs/__init__.py`
- `ecf/dgii/field_catalogs/tipo_ecf_31.py`
- `ecf/dgii/inventory_status.py`
- `ecf/dgii/types.py`
- `ecf/dgii/mapping.py`
- `ecf/management/commands/inspect_dgii_mapping.py`
- `tests/test_dgii_mapping.py`
- `CHECKPOINT_005_DGII_SOURCE_COLLECTION_AND_TIPO31_CATALOG.md` (this file)

Local ignored binaries under `docs/dgii/sources/` (not for commit):
- PDFs / XSD listed below

## Migrations

**No changes detected**

## Official files present locally

| file | status |
|---|---|
| `Informe_Tecnico_e-CF_v1.0.pdf` | collected |
| `Descripcion_Tecnica_Servicios_DGII.pdf` | collected |
| `Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | collected |
| `Formato_Aprobacion_Comercial_v1.0.pdf` | collected |
| `Representacion_Impresa_e-CF.pdf` | collected |
| `e-CF_31_v1.0.xsd` | collected |

Inventory helper summary: **6/11** priority official sources present locally.

## Official files still missing

| file | notes |
|---|---|
| `Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf` | portal listed; auto URL guesses 404 |
| `Formato_Acuse_de_Recibo_v1.0.pdf` | portal listed; auto URL guesses 404 |
| `Norma_General_01-2020.pdf` | legal library; not auto-found |
| `Ley_32-23.pdf` | legal library; not auto-found |
| `Decreto_587-24.pdf` | legal library; not auto-found |

Manual download instructions: `docs/dgii/sources/README.md`

## Tipo e-CF 31 catalog status

**Skeleton** — `SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW`

- Markdown catalog: `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- Python scaffold: `ecf/dgii/field_catalogs/tipo_ecf_31.py`
- XSD element names used only where visible in local `e-CF_31_v1.0.xsd`
- `REQUIRED_FIELDS` / `OPTIONAL_FIELDS` intentionally empty pending Formato obligation review
- Not marked reviewed/mapped

## Mapping command result summary (seeded invoice)

- Invoice: `BCC-AR-2026-000001`
- `future_catalog`: `TIPO_ECF_31`
- `catalog_status`: `SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW`
- `source_inventory_status`: 6/11 collected
- Status: `READY_FOR_FUTURE_DRAFT`
- Compliance: **NOT_DGII_COMPLIANT**
- Warning: `TIPO_ECF_31_CATALOG_PENDING_SOURCE_REVIEW`
- Warning: `MISSING_OFFICIAL_ENCF`
- Blocking issues: 0

## Final pytest result

**77 passed**

## Known limitations

- Catalog is skeleton; Formato PDF not fully reviewed field-by-field.
- Missing emitter-services PDF, ARECF format, and legal PDFs.
- No XML generation, XSD validation pipeline, signing, auth, or DGII submission.
- Official binaries are gitignored and must remain local-only unless policy changes.

## Exact next recommended task

Review local `Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` + `e-CF_31_v1.0.xsd` together to populate a **reviewed** Tipo 31 obligation matrix (`REQUIRED_FIELDS` / `OPTIONAL_FIELDS`) and promote catalog status beyond skeleton — still without generating production e-CF XML or calling DGII.
