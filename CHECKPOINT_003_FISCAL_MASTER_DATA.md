# CHECKPOINT 003 - Fiscal Master Data

branch: revamp/dgii-vault-mvp

test result: 14 passed

current models detected:
- Organization
- Contact
- Document
- Invoice
- InvoiceLine
- InternalDocumentCode
- ECFDocument
- AuditEvent

migration status:
- all existing migrations applied
- no pending migrations before changes

what will be changed:
- add fiscal master data models in `fiscal` app:
  - FiscalDocumentType
  - TaxRate
  - UnitOfMeasure
- add ProductService catalog in `invoicing` app
- add new invoice foreign key to `FiscalDocumentType` while preserving legacy string field
- add invoice line normalization with product, unit, tax rate references and historical snapshots
- add validation preventing issued invoice header/line edits
- update admin registrations for fiscal catalog and product/service models
- update `seed_bcc` to seed fiscal catalog, tax rates, units, product services, and a demo invoice
- add tests for fiscal master data, snapshots, and issued invoice safeguards

known limitations:
- no DGII submission, digital signing, or XML generation
- fiscal catalog is placeholder data for future e-CF readiness
- legacy `fiscal_document_type` string remains for backward compatibility
- invoice line calculations still use existing total logic and do not auto-generate XML
