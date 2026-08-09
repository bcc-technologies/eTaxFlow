# ecf/dgii — DGII mapping groundwork

Phase 005 package for mapping normalized eTaxFlow `Invoice` data to **future** DGII e-CF concepts.

## What this package does

- Builds read-only mapping reports (`build_invoice_dgii_mapping_report`)
- Documents field availability for issuer, customer, lines, totals, and identity codes
- Distinguishes `internal_code`, `official_ncf`, and `official_encf`

## What this package does **not** do

- Generate DGII-compliant XML
- Validate against official XSD
- Digitally sign XML
- Authenticate with DGII (semilla/token)
- Submit e-CF or poll TrackId
- Create `Document` or `ECFDocument` rows
- Claim compliance

See `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md` for official source documents that must be collected before compliance work.
