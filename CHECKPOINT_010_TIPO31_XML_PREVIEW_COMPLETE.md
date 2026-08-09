# Checkpoint 010 — Tipo 31 XML Preview Complete

## Files changed

- `CHECKPOINT_010_TIPO31_XML_PREVIEW_START.md` (new)
- `CHECKPOINT_010_TIPO31_XML_PREVIEW_COMPLETE.md` (new)
- `ecf/dgii/xml_preview/__init__.py` (new)
- `ecf/dgii/xml_preview/tipo_ecf_31_preview.py` (new)
- `ecf/dgii/xml_preview/documents.py` (new)
- `ecf/management/commands/generate_tipo31_preview_xml.py` (new)
- `invoicing/admin.py`
- `tests/test_tipo31_xml_preview.py` (new)
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`

## Migrations created

No changes detected

## Preview builder summary

`build_tipo31_xml_preview(invoice, allow_demo_encf=False, require_signing_placeholder=True) -> bytes`

- Root: `ETaxFlowTipo31EcfPreview`
- Attributes include `dgii_compliance=NOT_DGII_COMPLIANT`, `xml_signature=NOT_IMPLEMENTED`, `signature_field=MISSING`, `production_submission=FORBIDDEN`
- Deterministic element/line order and Decimal formatting
- Uses mapped invoice + reviewed Tipo 31 field matrix fields only
- FechaHoraFirma from existing `ECFDocument.signature_datetime` when present
- `SignaturePreview` is diagnostic only; no fake `<Signature>` / XMLDSig
- Validates Tipo 31, eNCF, sequence expiry, income/payment/billing, line snapshots, demo allow flag, optional signing placeholder

## Command behavior

`python manage.py generate_tipo31_preview_xml`

- `--internal-code` or `--invoice-id`
- Default: save/reuse Document
- `--stdout`: print XML, no Document
- `--allow-demo-encf` required for demo/non-authorized eNCF
- `--no-require-signing-placeholder` optional
- `--created-by` optional
- Does not create ECFDocument, sign, submit, or set TrackId

## Document generation behavior

`generate_tipo31_preview_document(...)`

- Saves `Document` (`XML` / `GENERATED` / `STORED`) linked to invoice
- Filename: `tipo31-preview-{internal_code}.xml`
- Internal code: `T31PREV-{internal_code}-{nnn}`
- AuditEvent: `tipo31_xml_preview_generated`

## Duplicate / reuse behavior

- Identical preview XML (same invoice + filename + sha256) reuses existing Document
- Changed invoice content (different hash) creates a new Document version

## Mapping result (seeded invoice after allocate + placeholder + preview)

- Status: `READY_FOR_FUTURE_DRAFT`
- Available field count: **21**
- Missing required: **1** — `Signature`
- Warnings include: `DEMO_OR_UNAUTHORIZED_ENCF`, `SIGNING_PLACEHOLDER_ONLY`
- Compliance: **NOT_DGII_COMPLIANT**

## Remaining missing required fields

1. `Signature`

## Preview generation result (local verification)

- First save: created `T31PREV-BCC-AR-2026-000001-001`
- Second save: reused same Document / hash
- `--stdout`: prints preview XML; no Document created
- Seed after `seed_bcc` had no eNCF/placeholder; ran `allocate_demo_encf` + `prepare_signing_placeholder` before preview

## Final pytest result

**130 passed**

## Known limitations

- Preview XML is not DGII e-CF XML and is not XSD-valid as a production instance
- Signature / XMLDSig remain unimplemented
- Demo eNCF is not DGII-authorized
- No TrackId, no DGII submission, no certificates/private keys

## Exact next recommended task

**Phase 011 — schema-aligned unsigned Tipo 31 XML draft (still non-production):** generate an unsigned XML closer to local `e-CF_31_v1.0.xsd` structure for laboratory comparison only, still leaving Signature missing, still forbidding production submission, and still **NOT_DGII_COMPLIANT** (no XMLDSig, no DGII calls, no TrackId).
