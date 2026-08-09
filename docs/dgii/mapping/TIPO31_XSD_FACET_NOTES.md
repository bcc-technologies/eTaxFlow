# Tipo 31 local XSD facet notes

Extracted from `docs/dgii/sources/e-CF_31_v1.0.xsd` using stdlib XML parsing.
**Synthetic / non-authorized.** Not DGII compliance evidence.

## eNCF

| item | value |
|---|---|
| field | `eNCF` |
| XSD type | `eNCFValidationType` |
| pattern | `([a-z0-9A-Z]{13})` |
| minLength | 13 |
| maxLength | 13 |
| element path | `ECF/Encabezado/IdDoc/eNCF` |
| element decl line | ~14 |
| type decl line | ~455 |
| prior demo value | `DEMO-E31-00000N` (15 chars, hyphens) — **fails** facets |
| proposed facet-safe demo value | `E31` + 10-digit padded number, e.g. `E319000000001` |
| safety note | Synthetic XSD-FACET-DEMO range only; **NOT DGII-authorized** |

## RNC (issuer / customer)

| item | value |
|---|---|
| fields | `RNCEmisor`, `RNCComprador` |
| XSD type | `RNCValidationType` |
| pattern | `[0-9]{11}\|[0-9]{9}` |
| length | exactly 9 or 11 digits |
| element paths | `ECF/Encabezado/Emisor/RNCEmisor`, `ECF/Encabezado/Comprador/RNCComprador` |
| type decl line | ~545 |
| prior issuer demo value | `1310000000` (10 digits) — **fails** |
| proposed issuer demo value | `131000001` (9 digits, synthetic) |
| customer demo value | `123456789` (already 9 digits) — OK |
| supplier demo value | `987654321` (already 9 digits) — OK |
| safety note | Synthetic seed values only; **not** verified real BCC RNC; **NOT DGII-authorized** |

## Local XSD defect (stub)

| item | value |
|---|---|
| issue | Element `IndicadorServicioTodoIncluido` references type `IndicadorServicioTodoIncluidoType` |
| declared type name in file | ` IndicadorServicioTodoIncluidoType` (leading space) ~line 476 |
| classification | `local_xsd_defect_or_stub` |
| lab workaround | experimental in-memory stub in Phase 012 validator — **not official** |

## Classification of Phase 012 errors

| error | classification |
|---|---|
| Signature / missing `xs:any` child | `intentional_unsigned_gap` |
| eNCF length/pattern with `DEMO-E31-` | `avoidable_demo_data_facet` |
| RNCEmisor 10-digit seed | `avoidable_demo_data_facet` |
| XSD type name whitespace mismatch | `local_xsd_defect_or_stub` |
