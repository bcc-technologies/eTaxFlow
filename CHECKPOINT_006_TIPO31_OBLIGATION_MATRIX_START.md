# Checkpoint 006 — Tipo e-CF 31 Obligation Matrix Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**77 passed**

## Collected source files

- `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf`
- `docs/dgii/sources/Descripcion_Tecnica_Servicios_DGII.pdf`
- `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf`
- `docs/dgii/sources/Formato_Aprobacion_Comercial_v1.0.pdf`
- `docs/dgii/sources/Representacion_Impresa_e-CF.pdf`
- `docs/dgii/sources/e-CF_31_v1.0.xsd`

## Missing source files

- Descripción Técnica Servicios Emisores Electrónicos
- Formato Acuse de Recibo v1.0
- Norma General 01-2020
- Ley 32-23
- Decreto 587-24

## Current Tipo 31 catalog status

`SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW`

## Intended scope

- Inspect local Formato e-CF v1.0 + XSD e-CF 31 v1.0
- Produce source notes and a reviewed field/obligation matrix
- Map availability against current eTaxFlow models
- Extend mapping report with catalog metrics
- Remain explicitly **NOT_DGII_COMPLIANT**

## Explicit non-goals

- Live DGII API calls
- Digital signing / certificate storage
- TrackId submission or polling
- Production e-CF XML generation
- Claiming DGII compliance
- Sending anything to DGII
