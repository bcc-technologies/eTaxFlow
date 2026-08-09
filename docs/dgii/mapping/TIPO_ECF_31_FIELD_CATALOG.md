# Tipo e-CF 31 Field Catalog (reviewed obligation matrix)

**Document type:** `31` — Factura de Crédito Fiscal Electrónica  
**Catalog status:** `REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT`  
**Compliance claim:** **NOT_DGII_COMPLIANT**

This catalog is a non-production mapping aid based on local official Formato e-CF v1.0 + XSD e-CF 31 v1.0 review. Phase 007 adds internal model support for several previously missing required fields. It does **not** authorize XML generation, signing, authentication, or DGII submission.

## 1. Source documents reviewed

| source | local_path | used_for | inspection_depth |
|---|---|---|---|
| Formato Comprobante Fiscal Electrónico (e-CF) V 1.0 | `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` | Obligation codes 0/1/2/3 for Tipo 31, field semantics, lengths | Text extract of Encabezado/Emisor/Comprador/Totales/Detalle/InformacionReferencia/FechaHoraFirma/Firma sections |
| XSD e-CF 31 v1.0 | `docs/dgii/sources/e-CF_31_v1.0.xsd` | Element names, hierarchy, minOccurs/maxOccurs, simpleType constraints | Full local XSD walk of ECF structure |
| Informe Técnico e-CF v1.0 | `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf` | Context only | Collected; not used for field obligations in this matrix |

Still missing for later phases: Emisores Electrónicos PDF, Acuse de Recibo, Norma 01-2020, Ley 32-23, Decreto 587-24.

## 2. Compliance status

- Official XML generation: **not implemented**
- XSD validation pipeline: **not implemented**
- Digital signature: **not implemented**
- DGII submission / TrackId: **not implemented**
- This catalog: **reviewed field matrix only — NOT_DGII_COMPLIANT**

## 3. Obligation matrix

| section | dgii_field_or_element | parent_path | required_status | type_or_format | length_or_precision | allowed_values | source_document | source_location | etaxflow_source_model | etaxflow_source_field | availability | mapping_notes | implementation_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Encabezado | Version | ECF/Encabezado | required | base=xs:decimal; enums=1.0 | enums=1.0 | 1.0 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.6 field #1 / XSD Encabezado/Version minOccurs=1 |  |  | derived | Constant 1.0 for future draft; not stored in Invoice. | pending |
| Encabezado | TipoeCF | ECF/Encabezado/IdDoc | required | base=xs:integer; enums=31\|32\|33\|34\|41\|43\|44\|45\|46\|47 | 2 | 31\|32\|33\|34\|41\|43\|44\|45\|46\|47 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.6 field #2 / XSD IdDoc/TipoeCF | FiscalDocumentType | code | available | Via Invoice.fiscal_document_type_ref.code (seed uses 31). | mapped |
| Encabezado | eNCF | ECF/Encabezado/IdDoc | required | base=xs:string; pattern=([a-z0-9A-Z]{13}); minLength=13; maxLength=13 | 13; pattern [A-Za-z0-9]{13} |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.6 field #3 / XSD IdDoc/eNCF | Invoice | official_encf | missing | Field exists but typically empty; no sequence assignment workflow yet. | pending |
| Encabezado | FechaVencimientoSecuencia | ECF/Encabezado/IdDoc | required | xs:string date dd-MM-yyyy | 10 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.6 field #4 / XSD IdDoc/FechaVencimientoSecuencia |  |  | missing | No eTaxFlow model field for authorized sequence expiry. | blocked |
| Encabezado | IndicadorEnvioDiferido | ECF/Encabezado/IdDoc | optional | base=xs:integer; enums=1 |  |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD IdDoc/IndicadorEnvioDiferido minOccurs=0; Formato PDF nearby IdDoc indicators |  |  | missing | No model field. | pending |
| Encabezado | IndicadorMontoGravado | ECF/Encabezado/IdDoc | conditional | base=xs:integer; enums=0\|1 | 1 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF IdDoc indicator section (Tipo31 code 2 in extract) / XSD minOccurs=0 |  |  | missing | Conditional when ITBIS included in line amounts. | pending |
| Encabezado | TipoIngresos | ECF/Encabezado/IdDoc | required | base=xs:string; enums=01\|02\|03\|04\|05\|06 | 2 | 01\|02\|03\|04\|05\|06 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.7 field #8 / XSD IdDoc/TipoIngresos |  |  | missing | No Invoice income-type field. | blocked |
| Encabezado | TipoPago | ECF/Encabezado/IdDoc | required | base=xs:integer; enums=1\|2\|3 | 1 | 1\|2\|3 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.7 field #9 / XSD IdDoc/TipoPago |  |  | missing | No payment-type field on Invoice. | blocked |
| Encabezado | FechaLimitePago | ECF/Encabezado/IdDoc | conditional | xs:string date dd-MM-yyyy | 10 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #10 (Tipo31=2) / XSD IdDoc/FechaLimitePago minOccurs=0 | Invoice | due_date | partially_available | due_date candidate when TipoPago=2 (crédito); format conversion needed. | pending |
| Encabezado | TerminoPago | ECF/Encabezado/IdDoc | optional | base=xs:string; pattern=[\s\d\w]{1,15} |  |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD IdDoc/TerminoPago; Formato PDF after FechaLimitePago |  |  | missing | No payment-term text field. | pending |
| Encabezado | TablaFormasPago | ECF/Encabezado/IdDoc | optional | complex |  |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.7-8 (Tipo31=3) / XSD IdDoc/TablaFormasPago minOccurs=0 |  |  | missing | No payment-forms table model. | pending |
| Encabezado | FormaPago | ECF/Encabezado/IdDoc/TablaFormasPago/FormaDePago | conditional | base=xs:integer; enums=1\|2\|3\|4\|5\|6\|7\|8 |  | 1\|2\|3\|4\|5\|6\|7\|8 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF FormaPago / XSD FormaDePago/FormaPago (required if parent present) |  |  | missing | Required only when TablaFormasPago is present. | pending |
| Encabezado | MontoPago | ECF/Encabezado/IdDoc/TablaFormasPago/FormaDePago | conditional | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD FormaDePago/MontoPago; Formato PDF payment table |  |  | missing | Required only when TablaFormasPago is present. | pending |
| Emisor | RNCEmisor | ECF/Encabezado/Emisor | required | base=xs:string; pattern=[0-9]{11}\|[0-9]{9} | 9 or 11 digits |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF ~p.9-10 field #20 / XSD Emisor/RNCEmisor | Organization | rnc | available | Issuer organization RNC. | mapped |
| Emisor | RazonSocialEmisor | ECF/Encabezado/Emisor | required | base=xs:string; minLength=1; maxLength=150 | 1-150 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #21 / XSD Emisor/RazonSocialEmisor | Organization | legal_name | available |  | mapped |
| Emisor | NombreComercial | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=150 | <=150 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #22 (Tipo31=3) / XSD Emisor/NombreComercial minOccurs=0 | Organization | commercial_name | available |  | mapped |
| Emisor | Sucursal | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=20 | <=20 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #23 (Tipo31=3) |  |  | missing | No branch/sucursal model. | pending |
| Emisor | DireccionEmisor | ECF/Encabezado/Emisor | required | base=xs:string; minLength=1; maxLength=100 | 1-100 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #24 / XSD Emisor/DireccionEmisor | Organization | address | partially_available | address exists but may exceed 100 chars / not structured for DGII. | mapped |
| Emisor | Municipio | ECF/Encabezado/Emisor | optional | xs:string/num code | 6 | Tabla III provinces/municipios | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #25 (Tipo31=3) |  |  | missing | No municipality code on Organization. | pending |
| Emisor | Provincia | ECF/Encabezado/Emisor | optional | xs:string/num code | 6 | Tabla III | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #26 (Tipo31=3) |  |  | missing | No province code on Organization. | pending |
| Emisor | TelefonoEmisor | ECF/Encabezado/Emisor/TablaTelefonoEmisor | optional | base=xs:string; pattern=\d{3}-\d{3}-\d{4}; maxLength=12 | 12; pattern ddd-ddd-dddd |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #27 (Tipo31=3) / XSD TablaTelefonoEmisor optional | Organization | phone | partially_available | phone exists; may not match xxx-xxx-xxxx pattern. | pending |
| Emisor | CorreoEmisor | ECF/Encabezado/Emisor | optional | base=xs:string; pattern=\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*; maxLength=80 | <=80 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #28 (Tipo31=3) | Organization | email | available |  | mapped |
| Emisor | WebSite | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=50 | <=50 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #29 (Tipo31=3) | Organization | website | partially_available | URLField may exceed 50 chars. | pending |
| Emisor | ActividadEconomica | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=100 | <=100 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #30 (Tipo31=3) |  |  | missing | No economic activity field. | pending |
| Emisor | CodigoVendedor | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=60 | <=60 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #31 (Tipo31=3) |  |  | missing |  | pending |
| Emisor | NumeroFacturaInterna | ECF/Encabezado/Emisor | optional | base=xs:string; minLength=1; maxLength=20 | <=20 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #32 (Tipo31=3) | Invoice | internal_code | partially_available | Candidate only; must remain distinct from eNCF. Length may exceed 20. | pending |
| Emisor | FechaEmision | ECF/Encabezado/Emisor | required | xs:string date dd-MM-yyyy | 10 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #37 / XSD Emisor/FechaEmision | Invoice | issue_date | available | Date format conversion to dd-MM-yyyy still required for XML. | mapped |
| Comprador | RNCComprador | ECF/Encabezado/Comprador | required | base=xs:string; pattern=[0-9]{11}\|[0-9]{9} | 9 or 11 digits |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #38 (Tipo31=1) / XSD Comprador/RNCComprador | Contact | rnc_or_id | partially_available | Available when id_type=RNC; format/length not validated to DGII pattern. | mapped |
| Comprador | RazonSocialComprador | ECF/Encabezado/Comprador | required | base=xs:string; minLength=1; maxLength=150 | 1-150 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #40 (Tipo31=1) / XSD Comprador/RazonSocialComprador | Contact | legal_name | available |  | mapped |
| Comprador | ContactoComprador | ECF/Encabezado/Comprador | optional | base=xs:string; minLength=1; maxLength=80 | see type_or_format |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD Comprador/ContactoComprador; Formato PDF Comprador section | Contact | commercial_name | partially_available | commercial_name is a candidate only. | pending |
| Comprador | CorreoComprador | ECF/Encabezado/Comprador | optional | base=xs:string; pattern=\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*; maxLength=80 | see type_or_format |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD Comprador/CorreoComprador | Contact | email | available |  | mapped |
| Comprador | DireccionComprador | ECF/Encabezado/Comprador | optional | base=xs:string; minLength=1; maxLength=100 | <=100 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #43 (Tipo31=3) | Contact | address | partially_available | address exists; length/structure not DGII-validated. | mapped |
| Comprador | MunicipioComprador | ECF/Encabezado/Comprador | optional | base=xs:string; enums=010000\|010100\|010101\|020000\|020100\|020101\|020102\|020103\|020104\|020105\|020106\|020107\|020108\|020109\|020200\|020201\|020202\|020300\|020301\|02030 | 6 | Tabla III | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #44 (Tipo31=3) |  |  | missing |  | pending |
| Comprador | ProvinciaComprador | ECF/Encabezado/Comprador | optional | base=xs:string; enums=010000\|010100\|010101\|020000\|020100\|020101\|020102\|020103\|020104\|020105\|020106\|020107\|020108\|020109\|020200\|020201\|020202\|020300\|020301\|02030 | 6 | Tabla III | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #45 (Tipo31=3) |  |  | missing |  | pending |
| Totales | MontoGravadoTotal | ECF/Encabezado/Totales | conditional | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #92 (Tipo31=2) / XSD Totales/MontoGravadoTotal minOccurs=0 | Invoice | subtotal | partially_available | subtotal is a candidate; ITBIS bucket split not modeled. | pending |
| Totales | MontoExento | ECF/Encabezado/Totales | conditional | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #96 (Tipo31=2) |  |  | missing | No dedicated exempt-total field. | pending |
| Totales | TotalITBIS | ECF/Encabezado/Totales | conditional | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #100 (Tipo31=2) / XSD Totales/TotalITBIS minOccurs=0 | Invoice | tax_total | partially_available | tax_total candidate; rate-bucket totals (TotalITBIS1/2/3) missing. | pending |
| Totales | MontoTotal | ECF/Encabezado/Totales | required | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #110 / XSD Totales/MontoTotal minOccurs=1 | Invoice | grand_total | available | grand_total maps conceptually to MontoTotal. | mapped |
| Totales | ValorPagar | ECF/Encabezado/Totales | optional | base=xs:decimal; pattern=[+-]?[0-9]{1,16}(.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF field #115 (Tipo31=3) / XSD Totales/ValorPagar minOccurs=0 | Invoice | grand_total | derived | Often equal to grand_total absent avance/saldo adjustments. | pending |
| DetallesItems | Item | ECF/DetallesItems | required | complex | maxOccurs=1000 |  | e-CF_31_v1.0.xsd; Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf | XSD DetallesItems/Item minOccurs=1; Formato PDF Detalle section | InvoiceLine | * | available | Invoice lines supply item rows. | mapped |
| DetallesItems | NumeroLinea | ECF/DetallesItems/Item | required | base=xs:integer; pattern=[0-9]{0,4}; totalDigits=4; minInclusive=1; maxInclusive=1000 | <=4 digits |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #1 (Tipo31=1) / XSD Item/NumeroLinea | InvoiceLine | line_order | available |  | mapped |
| DetallesItems | TipoCodigo | ECF/DetallesItems/Item/TablaCodigosItem/CodigosItem | conditional | base=xs:string; minLength=1; maxLength=14 | 1-14 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Tabla Códigos Ítem (Tipo31=3 for table) / XSD child required if table present |  |  | missing | No code-type enum stored; item_code_snapshot lacks TipoCodigo. | pending |
| DetallesItems | CodigoItem | ECF/DetallesItems/Item/TablaCodigosItem/CodigosItem | conditional | base=xs:string; minLength=1; maxLength=35 | 1-35 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Código del Ítem / XSD CodigosItem/CodigoItem | InvoiceLine | item_code_snapshot | partially_available | Snapshot can supply code value when TablaCodigosItem used. | pending |
| DetallesItems | IndicadorFacturacion | ECF/DetallesItems/Item | required | base=xs:integer; enums=0\|1\|2\|3\|4 | 1 | 0\|1\|2\|3\|4 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #4 (Tipo31=1) / XSD Item/IndicadorFacturacion | InvoiceLine | tax_rate_snapshot | missing | tax_rate_snapshot/tax_rate_ref are candidates but no explicit 0-4 indicator mapping implemented. | blocked |
| DetallesItems | NombreItem | ECF/DetallesItems/Item | required | base=xs:string; minLength=1; maxLength=80 | 1-80 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #8 (Tipo31=1) / XSD Item/NombreItem | InvoiceLine | item_name_snapshot | available | Fallback description possible if snapshot empty. | mapped |
| DetallesItems | IndicadorBienoServicio | ECF/DetallesItems/Item | required | base=xs:integer; enums=1\|2 | 1 | 1\|2 | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #9 (Tipo31=1) / XSD Item/IndicadorBienoServicio | ProductService | item_type | derived | Derive 1=PRODUCT, 2=SERVICE when product_service linked; blank if not linked. | pending |
| DetallesItems | DescripcionItem | ECF/DetallesItems/Item | optional | base=xs:string; minLength=1; maxLength=1000 | <=1000 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #10 (Tipo31=3) | InvoiceLine | description | available |  | mapped |
| DetallesItems | CantidadItem | ECF/DetallesItems/Item | required | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #11 (Tipo31=1) / XSD Item/CantidadItem | InvoiceLine | quantity | available |  | mapped |
| DetallesItems | UnidadMedida | ECF/DetallesItems/Item | optional | xs:string/num code | 2 | Tabla IV unidades | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #12 (Tipo31=3) | InvoiceLine | unit_snapshot | partially_available | Snapshot/unit FK exist; may not match DGII Tabla IV codes. | pending |
| DetallesItems | PrecioUnitarioItem | ECF/DetallesItems/Item | required | base=xs:decimal; pattern=(\d{1,16})(\.\d{1,4})?; totalDigits=20; fractionDigits=4 | up to 4 decimal places |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #25 (Tipo31=1) / XSD Item/PrecioUnitarioItem | InvoiceLine | unit_price | available |  | mapped |
| DetallesItems | DescuentoMonto | ECF/DetallesItems/Item | conditional | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #26 (Tipo31=2) | InvoiceLine | discount_amount | partially_available | discount_amount exists; SubDescuento table structure not modeled. | pending |
| DetallesItems | MontoItem | ECF/DetallesItems/Item | required | base=xs:decimal; pattern=[0-9]{1,16}(\.[0-9]{1,2})?; totalDigits=18; fractionDigits=2 | 18,2 |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Detalle field #39 (Tipo31=1) / XSD Item/MontoItem | InvoiceLine | line_total | derived | line_total is candidate; DGII MontoItem composition rules need future draft validation. | pending |
| InformacionReferencia | InformacionReferencia | ECF | conditional | complex |  |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF section summary Tipo31=2; XSD InformacionReferencia minOccurs=0 |  |  | not_applicable | Not used for ordinary Tipo 31 sales; required for NC/ND/contingency replacements. | pending |
| InformacionReferencia | NCFModificado | ECF/InformacionReferencia | conditional | base=xs:string; minLength=11; maxLength=19 | see type_or_format |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF InformacionReferencia / XSD InformacionReferencia children |  |  | missing | No modified-NCF reference model for Tipo 31 sales path. | pending |
| InformacionReferencia | CodigoModificacion | ECF/InformacionReferencia | conditional | xs:integer/string |  | PDF codes 1\|2\|3 primarily for NC/ND | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF Código de Modificación notes |  |  | not_applicable | Primarily NC/ND; not for standard Tipo 31 invoice. | pending |
| FechaHoraFirma | FechaHoraFirma | ECF | required | xs:string datetime | 19; dd-MM-yyyy HH:mm:ss |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF section G / XSD ECF/FechaHoraFirma minOccurs=1 |  |  | missing | Requires signing workflow (explicitly out of scope). | blocked |
| FirmaDigital | Signature | ECF | required | PDF tag &lt;Signature&gt;; XSD xs:any processContents=skip minOccurs=1 |  |  | Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf; e-CF_31_v1.0.xsd | Formato PDF section H tag &lt;Signature&gt;; XSD ECF sequence xs:any after FechaHoraFirma |  |  | missing | Digital signing explicitly out of scope; certificates not stored. | blocked |


## 3b. Phase 007/008 required-field model support

| dgii_field_or_element | etaxflow_source | catalog availability (model) | runtime notes | implementation_status |
|---|---|---|---|---|
| `eNCF` | `Invoice.official_encf` via `ENCFSequenceRange` | missing until allocated | Phase 008 demo allocation supported; **not DGII-authorized**; seed creates range only (no auto-allocate) | demo allocation supported / DGII authorization not implemented |
| `FechaVencimientoSecuencia` | `Invoice.sequence_expiration_date` | available when set | Nullable DateField; demo may populate synthetic expiry | mapped |
| `TipoIngresos` | `Invoice.income_type` → `FiscalIncomeType.code` | available when set | Catalog codes 01-06 from Formato/XSD review | mapped (preliminary) |
| `TipoPago` | `Invoice.payment_type` → `PaymentType.code` | available when set | Catalog codes 1\|2\|3 from Formato/XSD review | mapped (preliminary) |
| `IndicadorFacturacion` | `InvoiceLine.billing_indicator` → `BillingIndicator.code` | available when all lines set | Catalog codes 0-4 from Formato/XSD review | mapped (preliminary) |
| `FechaHoraFirma` | `ECFDocument.signature_datetime` | missing | Placeholder DateTimeField only; never set by seed/issue/XML draft | pending |
| `Signature` | future `ECFDocument.xml_signed_file` / signing service | missing | No signature blob, certificates, or private keys stored | blocked |

Still missing at runtime for a typical seeded invoice: **`eNCF`**, **`FechaHoraFirma`**, **`Signature`**.

## 4. Availability summary (57 catalog rows)

- available: **15**
- partially_available: **13**
- derived: **4**
- missing required: **7** — `eNCF`, `FechaVencimientoSecuencia`, `TipoIngresos`, `TipoPago`, `IndicadorFacturacion`, `FechaHoraFirma`, `Signature`

## 5. Fields currently available in eTaxFlow

- `TipoeCF` ← `FiscalDocumentType.code`
- `RNCEmisor` ← `Organization.rnc`
- `RazonSocialEmisor` ← `Organization.legal_name`
- `NombreComercial` ← `Organization.commercial_name`
- `CorreoEmisor` ← `Organization.email`
- `FechaEmision` ← `Invoice.issue_date`
- `RazonSocialComprador` ← `Contact.legal_name`
- `CorreoComprador` ← `Contact.email`
- `MontoTotal` ← `Invoice.grand_total`
- `Item` ← `InvoiceLine.*`
- `NumeroLinea` ← `InvoiceLine.line_order`
- `NombreItem` ← `InvoiceLine.item_name_snapshot`
- `DescripcionItem` ← `InvoiceLine.description`
- `CantidadItem` ← `InvoiceLine.quantity`
- `PrecioUnitarioItem` ← `InvoiceLine.unit_price`

## 6. Required fields still missing (runtime)

After Phase 007 model support, a seeded demo invoice typically still lacks:

- `eNCF` — empty until explicitly allocated from `ENCFSequenceRange` (`allocate_demo_encf` / admin action). Demo values remain **not DGII-authorized**.
- `FechaHoraFirma` — `ECFDocument.signature_datetime` placeholder exists but is never populated (signing not implemented).
- `Signature` — no signed XML / certificate storage; remains blocked until a dedicated signing phase.

Now model-supported (may be available when populated): `FechaVencimientoSecuencia`, `TipoIngresos`, `TipoPago`, `IndicadorFacturacion`, and demo `eNCF` after controlled allocation.

## 7. Ambiguities / open questions

1. Totales ITBIS / MontoGravado* are PDF conditional (code 2) and XSD optional — treated as conditional, not unconditionally required.
2. `NumeroFacturaInterna` may carry `internal_code` but must remain distinct from `eNCF`.
3. `IndicadorFacturacion` has no explicit eTaxFlow enum; tax_rate snapshot is insufficient alone.
4. `IndicadorBienoServicio` can be derived from `ProductService.item_type` only when a product link exists.
5. Buyer ID variants beyond RNC for credito fiscal need later confirmation against Emisores/legal sources still missing.
6. Signature / FechaHoraFirma remain blocked (signing out of scope).

## 8. Explicit non-goals

- Live DGII API calls
- Digital signing / certificate storage
- TrackId submission or polling
- Production e-CF XML generation
- Claiming DGII compliance
- Inventing DGII field names not visible in local sources
