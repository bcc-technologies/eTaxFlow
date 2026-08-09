# Checkpoint 007 — Tipo 31 Required Model Fields Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**79 passed**

## Current missing required Tipo 31 fields

1. `eNCF`
2. `FechaVencimientoSecuencia`
3. `TipoIngresos`
4. `TipoPago`
5. `IndicadorFacturacion`
6. `FechaHoraFirma`
7. `Signature`

## Intended scope

- Add nullable internal model/catalog support for missing required Tipo 31 data
- Admin + seed/demo wiring for preliminary values
- Mapping report evaluation against the new fields
- Keep compliance claim **NOT_DGII_COMPLIANT**

## Explicit non-goals

- Live DGII API calls
- Digital signing / certificate or private-key storage
- TrackId submission or polling
- Production e-CF XML generation
- Auto-generation of official eNCF
- Claiming DGII compliance
- Sending anything to DGII
