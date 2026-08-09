# Checkpoint 011 — Schema-Aligned Unsigned Tipo 31 Complete

## Files changed

- `CHECKPOINT_011_SCHEMA_ALIGNED_UNSIGNED_TIPO31_START.md` (new)
- `CHECKPOINT_011_SCHEMA_ALIGNED_UNSIGNED_TIPO31_COMPLETE.md` (new)
- `ecf/dgii/xsd/__init__.py` (new)
- `ecf/dgii/xsd/tipo_ecf_31_structure.py` (new)
- `ecf/dgii/xml_draft/__init__.py` (new)
- `ecf/dgii/xml_draft/tipo_ecf_31_unsigned.py` (new)
- `ecf/dgii/xml_draft/documents.py` (new)
- `ecf/management/commands/generate_tipo31_unsigned_draft.py` (new)
- `invoicing/admin.py`
- `tests/test_tipo31_unsigned_draft.py` (new)
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`

## Migrations created

No changes detected

## XSD structure extraction summary

From local `docs/dgii/sources/e-CF_31_v1.0.xsd` (stdlib `xml.etree` only):

- Root: `ECF`
- Top-level sequence: `Encabezado`, `DetallesItems`, `Subtotales`, `DescuentosORecargos`, `Paginacion`, `InformacionReferencia`, `FechaHoraFirma`, then required `xs:any` (Formato `<Signature>`)
- Required paths / optional paths extracted conservatively via `minOccurs`
- No network; no lxml; no instance validation pipeline

## Unsigned draft builder summary

`build_tipo31_unsigned_xml_draft(invoice, allow_demo_encf=False, require_signing_placeholder=True) -> bytes`

- Emits schema-shaped `ECF` XML with source-backed tags/order
- No preview-only compliance attributes on the root
- Omits Signature / xs:any (reported in diagnostics)
- Includes `eNCF`, mapped header/issuer/buyer/totals/items, and `FechaHoraFirma` from signing placeholder
- Deterministic decimals and line order (`line_order`, then `id`)

`Tipo31UnsignedDraftDiagnostics` reports `NOT_DGII_COMPLIANT`, missing Signature, demo/signing warnings, and `dgii_submission_allowed=False`.

## Command behavior

`python manage.py generate_tipo31_unsigned_draft`

- Default: save/reuse Document
- `--stdout`: print XML, no Document
- `--diagnostics-json`: print diagnostics JSON
- `--allow-demo-encf` required for demo/non-authorized eNCF
- Does not create ECFDocument, sign, submit, or set TrackId

## Document generation behavior

`generate_tipo31_unsigned_draft_document(...)`

- Filename: `tipo31-unsigned-draft-{internal_code}.xml`
- Internal code: `T31USGN-{internal_code}-{nnn}`
- AuditEvent: `tipo31_unsigned_draft_generated`

## Duplicate / reuse behavior

- Identical XML (same invoice + filename + sha256) reuses Document
- Content changes create a new Document version

## Diagnostics output summary

- `compliance_status`: `NOT_DGII_COMPLIANT`
- `draft_type`: `UNSIGNED_SCHEMA_ALIGNED_DRAFT`
- `root_name`: `ECF`
- `signature_present`: `false`
- `missing_required_fields`: `['Signature']`
- `uses_demo_encf`: `true` (for demo-allocated seeded invoice)
- `dgii_submission_allowed`: `false`

## Mapping result

After allocate + placeholder + unsigned draft:

- Status: `READY_FOR_FUTURE_DRAFT`
- Available: **21**
- Missing required: **1** — `Signature`
- Compliance: **NOT_DGII_COMPLIANT**

## Remaining missing required fields

1. `Signature`

## Final pytest result

**153 passed**

## Known limitations

- Unsigned draft is not DGII-submittable and is not fully XSD-valid as a production instance (Signature/xs:any omitted; demo eNCF may not match length-13 pattern)
- No XMLDSig / certificates / private keys
- No TrackId / DGII calls
- No full instance validation against XSD yet

## Exact next recommended task

**Phase 012 — local unsigned XSD instance validation report:** validate the generated unsigned `ECF` draft against local `e-CF_31_v1.0.xsd` using a safe installed/stdlib approach (or documented limitation if full validation needs an explicit dependency), produce a structured validation report that still marks **NOT_DGII_COMPLIANT**, and keep Signature missing / no DGII submission.
