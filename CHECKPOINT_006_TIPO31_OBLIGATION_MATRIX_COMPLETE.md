# Checkpoint 006 — Tipo e-CF 31 Obligation Matrix Complete

## Files changed

- `CHECKPOINT_006_TIPO31_OBLIGATION_MATRIX_START.md` (new)
- `CHECKPOINT_006_TIPO31_OBLIGATION_MATRIX_COMPLETE.md` (new)
- `docs/dgii/mapping/TIPO_ECF_31_SOURCE_NOTES.md` (new)
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md` (updated — reviewed matrix)
- `ecf/dgii/field_catalogs/tipo_ecf_31.py` (updated — reviewed machine-readable catalog)
- `ecf/dgii/field_catalogs/__init__.py`
- `ecf/dgii/mapping.py`
- `ecf/dgii/types.py`
- `ecf/management/commands/inspect_dgii_mapping.py`
- `tests/test_dgii_mapping.py`
- `README.md`

## Migrations created

**No changes detected**

## Source files reviewed

- `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf`
- `docs/dgii/sources/e-CF_31_v1.0.xsd`
- Context: `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf`

## Field catalog status

`REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT`

## Number of fields extracted

**57** catalog rows in the reviewed obligation matrix

## Missing required fields count

**7**

- `eNCF`
- `FechaVencimientoSecuencia`
- `TipoIngresos`
- `TipoPago`
- `IndicadorFacturacion`
- `FechaHoraFirma`
- `Signature` (PDF tag; XSD encodes as required `xs:any`)

## Mapping command summary for seeded invoice

- Invoice: `BCC-AR-2026-000001`
- Status: `READY_FOR_FUTURE_DRAFT`
- Catalog status: `REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT`
- Available fields: **15**
- Partially available: **13**
- Derived: **4**
- Missing required: **7**
- Compliance claim: **NOT_DGII_COMPLIANT**
- No Document / ECFDocument created by mapping inspection

## Final pytest result

**79 passed**

## Known limitations

- Still missing Emisores Electrónicos, Acuse de Recibo, Norma 01-2020, Ley 32-23, Decreto 587-24.
- Catalog covers sales-focused Tipo 31 obligations; specialized ISC/mining/OtraMoneda branches are only lightly noted.
- No production XML generation, XSD instance validation, signing, or DGII submission.
- Several required DGII concepts have no eTaxFlow model yet (`TipoIngresos`, `TipoPago`, sequence expiry, billing indicator, signature datetime).
- PDF conditional Totales ITBIS buckets remain unresolved for deterministic mapping from a single `tax_total`.

## Exact next recommended task

**Collect remaining official sources** (Emisores Electrónicos + Acuse de Recibo + Norma/Ley/Decreto), then design eTaxFlow model fields for the 7 missing required Tipo 31 catalog items (`eNCF` assignment workflow, `FechaVencimientoSecuencia`, `TipoIngresos`, `TipoPago`, `IndicadorFacturacion`) — still without signing, TrackId, or production XML.
