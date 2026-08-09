# Tipo e-CF 31 Field Catalog (skeleton)

**Document type:** `31` — Factura de Crédito Fiscal Electrónica  
**Catalog status:** `SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW`  
**Compliance claim:** **NOT_DGII_COMPLIANT**

This catalog is a non-production mapping aid. It does **not** authorize XML generation, signing, authentication, or DGII submission.

## 1. Source documents used

| source | local_path | used_for | inspection_depth |
|---|---|---|---|
| XSD e-CF 31 v1.0 | `docs/dgii/sources/e-CF_31_v1.0.xsd` | XML element names / structural skeleton | element names + selected `minOccurs` from XSD root sections |
| Formato Comprobante Fiscal Electrónico (e-CF) V 1.0 | `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | future obligation/semantics review | collected; full field-by-field review **PENDING** |
| Informe Técnico e-CF v1.0 | `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf` | context | collected; not fully reviewed here |
| Representación Impresa e-CF | `docs/dgii/sources/Representacion_Impresa_e-CF.pdf` | print section placeholder | collected; not mapped |

Missing priority sources still needed for a reviewed catalog:
- Descripción Técnica Servicios Emisores Electrónicos
- Formato Acuse de Recibo v1.0
- Norma General 01-2020 / Ley 32-23 / Decreto 587-24

## 2. Compliance status

- Official XML generation: **not implemented**
- XSD validation pipeline: **not implemented**
- Digital signature: **not implemented**
- DGII submission / TrackId: **not implemented**
- This catalog: **skeleton only**

## 3. Header / Encabezado fields

Element names below are **directly visible** in local `e-CF_31_v1.0.xsd` under `ECF/Encabezado/IdDoc` (and Version). Obligation semantics beyond XSD `minOccurs` remain **PENDING** Formato PDF review.

| xml_element (from local XSD) | xsd_minOccurs (as seen) | etaxflow_source | status |
|---|---|---|---|
| `Version` | 1 | TODO / pending mapping | PENDING |
| `TipoeCF` | 1 | `fiscal_document_type_ref.code` (concept) | PENDING review |
| `eNCF` | 1 | `official_encf` (future assignment) | PENDING / currently absent in seed |
| `FechaVencimientoSecuencia` | 1 | missing in eTaxFlow | PENDING / MISSING |
| `TipoIngresos` | 1 | missing in eTaxFlow | PENDING / MISSING |
| `TipoPago` | 1 | missing in eTaxFlow | PENDING / MISSING |
| `IndicadorEnvioDiferido` | 0 | missing | PENDING |
| `IndicadorMontoGravado` | 0 | missing | PENDING |
| `IndicadorServicioTodoIncluido` | 0 | missing | PENDING |
| `FechaLimitePago` | 0 | `Invoice.due_date` (candidate) | PENDING |
| `TerminoPago` | 0 | missing | PENDING |
| `FechaEmision` | TODO confirm path in XSD Totales/IdDoc area | `Invoice.issue_date` (candidate) | PENDING |

## 4. Issuer / Emisor fields

Visible under XSD `Emisor` (names from local XSD):

| xml_element (from local XSD) | etaxflow_source | status |
|---|---|---|
| `RNCEmisor` | `Organization.rnc` | PENDING review |
| `RazonSocialEmisor` | `Organization.legal_name` | PENDING review |
| `NombreComercial` | `Organization.commercial_name` | PENDING review |
| `DireccionEmisor` | `Organization.address` | PENDING review |
| `CorreoEmisor` | `Organization.email` | PENDING review |
| `TablaTelefonoEmisor` / `TelefonoEmisor` | `Organization.phone` (candidate) | PENDING |
| `WebSite` | `Organization.website` (candidate) | PENDING |
| `ActividadEconomica` | missing | PENDING / MISSING |
| `CodigoVendedor` | missing | PENDING / MISSING |
| `NumeroFacturaInterna` | `Invoice.internal_code` (candidate only; not e-NCF) | PENDING — must remain distinct from `eNCF` |
| `NumeroPedidoInterno` | missing | PENDING |
| `ZonaVenta` / `RutaVenta` / `InformacionAdicionalEmisor` | missing | PENDING |

## 5. Buyer / Comprador fields

Visible under XSD `Comprador`:

| xml_element (from local XSD) | etaxflow_source | status |
|---|---|---|
| `RNCComprador` | `Contact.rnc_or_id` (when id_type=RNC) | PENDING review |
| `RazonSocialComprador` | `Contact.legal_name` | PENDING review |
| `ContactoComprador` | missing / commercial_name candidate | PENDING |
| `CorreoComprador` | `Contact.email` | PENDING review |
| `DireccionComprador` | `Contact.address` | PENDING review |
| `MunicipioComprador` | missing | PENDING / MISSING |
| `ProvinciaComprador` | missing | PENDING / MISSING |
| `FechaEntrega` / `ContactoEntrega` / `DireccionEntrega` | missing | PENDING |
| `IdentificadorAdicional` style fields | missing | TODO confirm exact XSD members before mapping |

## 6. Line item / Detalle fields

Visible under XSD `DetallesItems` / `Item` (selected):

| xml_element (from local XSD) | etaxflow_source | status |
|---|---|---|
| `NumeroLinea` | `InvoiceLine.line_order` | PENDING review |
| `IndicadorFacturacion` | missing | PENDING / MISSING |
| `NombreItem` | `item_name_snapshot` / product name | PENDING review |
| `IndicadorBienoServicio` | `ProductService.item_type` candidate | PENDING |
| `DescripcionItem` | `InvoiceLine.description` | PENDING review |
| `CantidadItem` | `InvoiceLine.quantity` | PENDING review |
| `UnidadMedida` | `unit_snapshot` / `UnitOfMeasure.code` | PENDING review |
| `PrecioUnitarioItem` | `InvoiceLine.unit_price` | PENDING review |
| `DescuentoMonto` | `InvoiceLine.discount_amount` | PENDING review |
| `RecargoMonto` | missing | PENDING |
| `TablaCodigosItem` / `CodigoItem` / `TipoCodigo` | `item_code_snapshot` candidate | PENDING |
| `MontoItem` | `InvoiceLine.line_total` / taxable base TBD | PENDING — semantics need Formato review |
| ITBIS / impuesto members (`ITBIS1`… / adicionales) | `tax_amount` / `tax_rate_ref` candidates | PENDING |

## 7. Totals fields

Visible under XSD `Totales` (selected):

| xml_element (from local XSD) | etaxflow_source | status |
|---|---|---|
| `MontoGravadoTotal` | `Invoice.subtotal` candidate | PENDING |
| `MontoExento` | missing dedicated field | PENDING / MISSING |
| `TotalITBIS` | `Invoice.tax_total` candidate | PENDING |
| `MontoTotal` | `Invoice.grand_total` candidate | PENDING |
| `MontoNoFacturable` | missing | PENDING |
| other `MontoGravadoI1/I2/I3`, `TotalITBIS1/2/3` | missing rate-bucket fields | PENDING / MISSING |

## 8. References / modifications fields

Visible XSD area: `InformacionReferencia` / `NCFModificado` / `FechaNCFModificado` / `CodigoModificacion`.

| topic | status |
|---|---|
| Credit/debit note references | TODO / PENDING — not mapped for Tipo 31 sales invoice yet |
| Contingency replacement references | TODO / PENDING |

## 9. Printed representation fields

| topic | status |
|---|---|
| Representación Impresa models | local PDF collected; field mapping TODO / PENDING |
| eTaxFlow print layer | not implemented |

## 10. Fields currently available in eTaxFlow

High-confidence internal fields useful for a *future* Tipo 31 draft (not compliance):

- `Invoice.internal_code` (vault id; **not** `eNCF`)
- `Invoice.official_ncf` / `Invoice.official_encf` (currently empty on seed)
- `Invoice.fiscal_document_type_ref.code` (`31`)
- `Invoice.issue_date`, `due_date`, `currency`
- `Invoice.subtotal`, `discount_total`, `tax_total`, `grand_total`
- `Organization.rnc`, `legal_name`, `commercial_name`, `address`, `phone`, `email`, `website`
- `Contact.rnc_or_id`, `id_type`, `legal_name`, `commercial_name`, `address`, `phone`, `email`
- `InvoiceLine.line_order`, `description`, `quantity`, `unit_price`, `discount_amount`, `tax_rate`, `tax_amount`, `line_total`
- line snapshots: `item_code_snapshot`, `item_name_snapshot`, `unit_snapshot`, `tax_rate_snapshot`, `currency_snapshot`

## 11. Fields missing in eTaxFlow

Examples (not exhaustive; confirmed needed by XSD visibility and current model gaps):

- Assigned official `eNCF` sequence management
- `FechaVencimientoSecuencia`
- `TipoIngresos`, `TipoPago`, payment table (`TablaFormasPago`)
- Economic activity code for issuer
- Buyer municipio/provincia
- DGII `IndicadorFacturacion` / `IndicadorBienoServicio` explicit fields
- ITBIS rate buckets (I1/I2/I3) and additional taxes model
- Reference/modification blocks for NC/ND
- Digital signature block (out of scope)

## 12. Open questions

1. Exact obligation matrix for Tipo 31 from Formato e-CF PDF vs XSD `minOccurs` — PENDING review.
2. Whether `NumeroFacturaInterna` should carry `internal_code` or a separate DGII-facing internal invoice number.
3. How to map ITBIS buckets when eTaxFlow currently stores a single `tax_total`.
4. Required buyer ID variants beyond RNC for credito fiscal use cases.
5. Sequence/range (`FechaVencimientoSecuencia`) data ownership in eTaxFlow.

## 13. Explicit non-goals

- Live DGII API calls
- Digital signing / certificate storage
- TrackId submission or polling
- Production e-CF XML generation
- Claiming DGII compliance
- Inventing missing official documents or field names
