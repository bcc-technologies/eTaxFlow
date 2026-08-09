# Tipo e-CF 31 Source Extraction Notes

**Date inspected:** 2026-08-09  
**Branch context:** Phase 006 obligation matrix  
**Catalog status after review:** `REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT`

## Source file names inspected

| file | path | role |
|---|---|---|
| Formato e-CF v1.0 | `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | Obligation codes and field semantics for Tipo 31 |
| XSD e-CF 31 v1.0 | `docs/dgii/sources/e-CF_31_v1.0.xsd` | Element hierarchy, minOccurs, simpleType constraints |
| Informe Técnico e-CF v1.0 | `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf` | Context only (not used for obligation cells) |

## Extraction method

1. Confirmed local binary presence under `docs/dgii/sources/` (gitignored binaries still readable locally).
2. Extracted Formato PDF text with `pdftotext` to a temporary text dump.
3. Walked local XSD with Python `xml.etree.ElementTree`, recording element name, parent path, minOccurs/maxOccurs, and resolved simpleType constraints.
4. Cross-walked Formato PDF Tipo 31 obligation column (codes `0/1/2/3`) against XSD structure for Encabezado, Emisor, Comprador, Totales, DetallesItems, InformacionReferencia, FechaHoraFirma, and Signature.
5. Mapped each reviewed field to current eTaxFlow models conservatively (`available` / `partially_available` / `derived` / `missing` / `not_applicable`).

## Sections / pages from PDF inspected

Approximate page markers from the text extract (Formato PDF “Pág. X de 87”):

- Obligation legend: ~p.4 (codes 0/1/2/3)
- Encabezado / IdDoc start: ~p.6–8 (`Version`, `TipoeCF`, `eNCF`, `FechaVencimientoSecuencia`, `TipoIngresos`, `TipoPago`, payment table)
- Emisor: ~p.9–12 (`RNCEmisor`, `RazonSocialEmisor`, address/contact, `FechaEmision`)
- Comprador: ~p.12+ (`RNCComprador`, `RazonSocialComprador`, address fields)
- Totales: later Encabezado Totales block (`MontoGravadoTotal`, `MontoExento`, `TotalITBIS`, `MontoTotal`, `ValorPagar`)
- Detalle / Item: Detalle de Bienes o Servicios (`NumeroLinea`, `IndicadorFacturacion`, `NombreItem`, `IndicadorBienoServicio`, quantities/prices, `MontoItem`)
- InformacionReferencia: section F / detailed reference table
- FechaHoraFirma + Signature: sections G/H (~end of document body)

Exact PDF page numbers can vary by viewer; locations in the catalog cite field numbers / XSD paths as the primary anchors.

## XSD elements / types inspected

- Root `ECF` children including `Encabezado`, `DetallesItems`, `InformacionReferencia`, `FechaHoraFirma`, `Signature`
- `Encabezado`: `Version`, `IdDoc`, `Emisor`, `Comprador`, `Totales`, optional `OtraMoneda`
- `IdDoc`: `TipoeCF`, `eNCF`, `FechaVencimientoSecuencia`, indicators, `TipoIngresos`, `TipoPago`, `TablaFormasPago`
- `Emisor` / `Comprador` required identity and address members (`minOccurs`)
- `DetallesItems/Item` required leafs: `NumeroLinea`, `IndicadorFacturacion`, `NombreItem`, `IndicadorBienoServicio`, `CantidadItem`, `PrecioUnitarioItem`, `MontoItem`
- Nested optional tables: `TablaCodigosItem`, `TablaSubDescuento`, `TablaTelefonoEmisor`, `ImpuestosAdicionales`
- SimpleTypes for decimal patterns, date `dd-MM-yyyy`, datetime `dd-MM-yyyy HH:mm:ss`, TipoeCF enums, IndicadorFacturacion enums, etc.

## Unresolved ambiguities

1. Several Totales amount fields are PDF **conditional (2)** while XSD marks them `minOccurs=0` — recorded as `conditional`, not `required`.
2. Nested children can be XSD-required only when an optional parent table is present (e.g. `FormaPago`, `TelefonoEmisor`) — recorded as `conditional`.
3. `InformacionReferencia` is PDF section-code **2** for Tipo 31 (conditional), primarily for contingency/NC-ND style references — marked `not_applicable` for ordinary sales invoices.
4. Some Formato text cells are OCR/layout-noisy (split tags / footnote digits glued to obligation columns). Where noisy, XSD `minOccurs` was preferred and PDF noted as supporting context.
5. Printed-representation (RI) column `I` was not expanded into a full RI matrix in this phase.

## Fields requiring confirmation

- Exact buyer ID handling when `Contact.id_type` is not RNC (cedula/passport) for credito fiscal.
- Whether `NumeroFacturaInterna` should reuse `Invoice.internal_code` despite length (`internal_code` may exceed 20).
- Mapping rules from `tax_rate` / `tax_rate_ref` / snapshots → `IndicadorFacturacion` (0–4).
- Whether seeded phone values can be normalized to `xxx-xxx-xxxx` for `TelefonoEmisor`.
- Ownership model for authorized e-NCF ranges and `FechaVencimientoSecuencia`.

## Fields in XSD but not clearly explained in PDF extract

- Several nested OtraMoneda / ImpuestoAdicionalOtraMoneda members (structure visible in XSD; PDF explains other-currency printing as conditional).
- Some mining / ISC specialized Item children present in XSD; Formato explains them as specialized conditional cases — not fully expanded in this Tipo 31 sales-focused matrix.
- Formato PDF names the digital signature tag `<Signature>`, while local XSD encodes it as required `xs:any processContents="skip"` after `FechaHoraFirma` (no named Signature element in the XSD).

## Fields explained in PDF but not clearly constrained in XSD

- Business rules such as “gratuito (TipoPago=3) invalid for credito fiscal” are PDF narrative, not XSD enumerations beyond allowing value `3`.
- Printability column (`I`/`N`/`P`) is PDF-only; XSD does not encode representation impresa obligations.
- Conditional cross-field rules (e.g. FechaLimitePago required when TipoPago=crédito) are PDF narrative; XSD leaves FechaLimitePago optional.

## Explicit non-claims

- This extraction does **not** claim DGII compliance.
- This extraction does **not** generate production e-CF XML.
- Missing legal/service documents were not invented.
