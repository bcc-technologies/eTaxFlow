# eTaxFlow

eTaxFlow is a Django-based MVP for internal invoice vaulting and invoicing workflows for BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python manage.py migrate
python -m pytest -q
python manage.py runserver
```

## Seed demo data

```bash
python manage.py seed_bcc
```

Diagnose and optionally clean duplicate demo/seed rows:

```bash
python manage.py diagnose_seed_duplicates
python manage.py cleanup_seed_demo_data          # dry-run (default)
python manage.py cleanup_seed_demo_data --apply  # mutate clearly-demo duplicates only
```

Explicit opt-in merge for ambiguous duplicate contacts (never automatic):

```bash
python manage.py merge_duplicate_contacts \
  --contact-type CLIENT --rnc-or-id 123456789 --keep-pk 1 --dry-run
python manage.py merge_duplicate_contacts \
  --contact-type CLIENT --rnc-or-id 123456789 --keep-pk 1 --apply \
  --reason "Resolve local demo duplicate contacts"
```

**Contact uniqueness warning:** `(contact_type, rnc_or_id)` is a soft/business-level natural key only. It is **not** enforced with a database `UniqueConstraint` yet, because local databases may already contain duplicates. Prefer `contacts.natural_keys.resolve_contact_by_natural_key` for deterministic resolution.

## Admin workflow

- Use the Django admin to create and manage organizations, contacts, invoices, documents, and ECF placeholders.
- Invoice totals are calculated automatically and are read-only in admin.
- Invoice lifecycle transitions are enforced through safe state methods.
- Document invoice links create audit events when a document is associated with an invoice.

## Fiscal master data

This project now includes preliminary internal fiscal master data for demo and workflow development:

- `FiscalDocumentType`
- `TaxRate`
- `UnitOfMeasure`
- `ProductService`
- line-item snapshot fields for invoice persistence

## Internal XML draft layer

- Generate internal XML draft documents for invoices using `python manage.py generate_internal_xml --invoice <INVOICE_CODE>` or `python manage.py generate_internal_xml --all`
- Use the admin action `Generate internal XML draft documents` on invoices to create XML artifacts from normalized invoice data.
- This XML is a deterministic internal draft only and not DGII-compliant or signed.

## DGII schema mapping groundwork

Phase 005 maps existing normalized invoice data to **future** DGII e-CF concepts only.

```bash
python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001
python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001 --json
python manage.py inspect_dgii_mapping --invoice-id 1 --strict
```

- Inventory of official DGII source documents: `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`
- Mapping package: `ecf/dgii/`
- This phase does **not** generate DGII-compliant XML
- It does **not** digitally sign
- It does **not** authenticate with DGII (semilla/token)
- It does **not** send anything to DGII
- Official DGII documents must be collected and reviewed before claiming compliance

## Tipo e-CF 31 field catalog

Phase 006 reviewed local official sources and produced a Tipo e-CF 31 obligation matrix:

- `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf`
- `docs/dgii/sources/e-CF_31_v1.0.xsd`
- Context: `docs/dgii/sources/Informe_Tecnico_e-CF_v1.0.pdf`

Artifacts:

- Human matrix: `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- Source notes: `docs/dgii/mapping/TIPO_ECF_31_SOURCE_NOTES.md`
- Machine-readable catalog: `ecf/dgii/field_catalogs/tipo_ecf_31.py`

The matrix records DGII field/element names, parent paths, required/optional/conditional status from Formato+XSD, types/constraints, eTaxFlow model availability (`available` / `partially_available` / `derived` / `missing` / `not_applicable`), and implementation status.

Currently available eTaxFlow sources include issuer/customer identity basics, invoice dates/totals, and line quantity/price/name snapshots. Still missing required catalog fields such as assigned `eNCF`, `FechaVencimientoSecuencia`, `TipoIngresos`, `TipoPago`, explicit `IndicadorFacturacion`, plus signing fields (`FechaHoraFirma`, `Signature`).

This remains **NOT_DGII_COMPLIANT** and not production-ready: no official XML generation, no XSD validation pipeline, no digital signing, and no DGII submission/TrackId.

## Tipo 31 required data model support

Phase 007 adds internal model support for previously missing required Tipo 31 concepts:

| DGII concept | eTaxFlow source |
|---|---|
| `eNCF` | existing nullable `Invoice.official_encf` (not auto-generated) |
| `FechaVencimientoSecuencia` | `Invoice.sequence_expiration_date` |
| `TipoIngresos` | `FiscalIncomeType` + `Invoice.income_type` |
| `TipoPago` | `PaymentType` + `Invoice.payment_type` |
| `IndicadorFacturacion` | `BillingIndicator` + `InvoiceLine.billing_indicator` |
| `FechaHoraFirma` | `ECFDocument.signature_datetime` placeholder only |
| `Signature` | still missing (future signed XML / signing service) |

`seed_bcc` populates preliminary income/payment/billing catalogs (codes from Formato/XSD review) and demo invoice/line FKs, plus a synthetic sequence expiry. It does **not** assign `official_encf` and does **not** set `signature_datetime`.

Still missing for DGII-style readiness: assigned official eNCF, real signing datetime, and digital signature material. Official eNCF generation is intentionally unimplemented (needs authorized sequences / DGII workflow). Signature remains missing because certificates/private keys and signing are out of scope.

This still does **not** produce DGII-compliant XML.

## Non-production eNCF sequence allocation

Phase 008 adds `ENCFSequenceRange` (fiscal app) for local, controlled eNCF assignment into `Invoice.official_encf`.

```bash
python manage.py seed_bcc   # creates DEMO DEV range only; does not allocate
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --dry-run
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --allow-demo --apply
```

- Demo seed range uses prefix `DEMO-E31-` + zero-padded numbers (local format; not claimed as XSD/DGII-authorized).
- Allocation requires `--allow-demo` for unauthorized/demo ranges and never silently uses production.
- PRODUCTION ranges must set `is_authorized_by_dgii=True` in the model; this app does **not** obtain DGII authorization.
- `official_encf` remains controlled: not auto-generated by seed or invoice issue transitions.
- Mapping reports warn when eNCF looks demo/non-authorized and stay **NOT_DGII_COMPLIANT**.
- Allocation does not create signed XML or store certificates.

## Non-production signing placeholder

Phase 009 adds an explicit UNSIGNED → SIGNING_PLACEHOLDER workflow on `ECFDocument` for local FechaHoraFirma mapping only.

```bash
python manage.py seed_bcc
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --allow-demo --apply
python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --dry-run
python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --apply --note "Local placeholder only; no real digital signature"
python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001
```

- `FechaHoraFirma` can be represented internally via `ECFDocument.signature_datetime` after `prepare_signing_placeholder`.
- This is **not** a real digital signature timestamp and does not perform XMLDSig.
- `Signature` remains missing — no certificates, private keys, or signed XML artifacts are stored.
- `attempt_real_signing()` is an explicit blocker (`NotImplementedError`).
- Mapping warns with `SIGNING_PLACEHOLDER_ONLY` and remains **NOT_DGII_COMPLIANT**.
- `seed_bcc` does **not** auto-create a signing placeholder.

## Tipo 31 XML preview

Phase 010 adds a non-production **structure preview** XML for Tipo e-CF 31 (`ETaxFlowTipo31EcfPreview`). It is deterministic, marked `NOT_DGII_COMPLIANT`, leaves Signature missing, and never calls DGII.

```bash
python manage.py seed_bcc
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --allow-demo --apply
python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --apply --note "Local placeholder only; no real digital signature"
python manage.py generate_tipo31_preview_xml --internal-code BCC-AR-2026-000001 --allow-demo-encf
python manage.py generate_tipo31_preview_xml --internal-code BCC-AR-2026-000001 --allow-demo-encf --stdout
```

- Default mode saves/reuses an internal `Document` (`tipo31-preview-…xml`) with sha256 idempotence.
- `--stdout` prints XML and does **not** create a Document.
- Demo/non-authorized eNCF requires `--allow-demo-encf`.
- Preview does **not** create `ECFDocument`, signed XML, TrackId, or DGII submissions.

### Warnings

- Preview XML is **not** DGII e-CF XML.
- Not signed (Signature missing; XMLDSig not implemented).
- No TrackId.
- No DGII submission.
- Demo eNCF is not authorized.

## Tipo 31 unsigned schema-aligned draft

Phase 011 generates an **unsigned**, schema-shaped Tipo e-CF 31 draft rooted at XSD `ECF`, using source-backed tags/order from the local XSD and reviewed field matrix. Signature remains omitted. Status stays **NOT_DGII_COMPLIANT** in diagnostics (not as schema-root attributes).

```bash
python manage.py seed_bcc
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --allow-demo --apply
python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --apply --note "Local placeholder only; no real digital signature"
python manage.py generate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf
python manage.py generate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --stdout
python manage.py generate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --diagnostics-json
```

### Warnings

- Unsigned draft is **not** valid for DGII submission.
- No XMLDSig / no certificate / no private keys.
- No TrackId.
- Demo eNCF is not authorized.
- Output must be validated later against the official XSD after a real signing path is designed.

## Local Tipo 31 XSD validation

Phase 012 runs an offline XSD validation experiment against `docs/dgii/sources/e-CF_31_v1.0.xsd` using `lxml` (added because Python stdlib cannot validate XSD).

```bash
python manage.py generate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf
python manage.py validate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf
python manage.py validate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --json
python manage.py validate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --write-report /tmp/tipo31_unsigned_validation.md
```

### Warnings

- Validation failure is **expected** for unsigned drafts (Signature missing).
- This is **not** certification evidence and **not** DGII compliance.
- No signing / authentication / DGII submission exists.
- Local XSD may need an experimental type stub to compile; that stub is not official.

## Demo facet hardening (Phase 013)

Phase 013 reduces **avoidable** local XSD facet noise from seed/demo data. It does **not** implement signing, DGII submission, or compliance.

Adjusted synthetic demo values (see `core/demo_profiles.py` and `docs/dgii/mapping/TIPO31_XSD_FACET_NOTES.md`):

- Issuer RNC: `131000001` (9 digits; local `RNCValidationType`) — synthetic, not a verified real BCC RNC
- Customer / supplier RNCs remain 9-digit synthetic values
- Optional `XSD_FACET_DEMO` eNCF range: prefix `E31` + 10 digits (13 alphanumeric chars; local `eNCFValidationType`) — still `is_authorized_by_dgii=False`, `environment=DEV`

Classic `DEMO-E31-` range remains the default allocation path. Facet-safe eNCF requires an explicit flag:

```bash
python manage.py seed_bcc
python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --xsd-facet-demo --allow-demo --apply
python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --apply --note "Local placeholder only; no real digital signature"
python manage.py generate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf
python manage.py validate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --json
```

Validation reports group errors (`signature_missing_expected`, `demo_facet_mismatch`, `local_xsd_stub_required`, etc.). After facet-safe seed/allocation, `avoidable_demo_facet_error_count` should drop; Signature remains intentionally missing and status stays `NOT_DGII_COMPLIANT`.

## Warnings

- `internal_code` is not the same as DGII official `NCF` or `e-NCF`.
- Fiscal catalog data is preliminary internal master data and placeholder-only.
- Production DGII e-CF XML generation / submission is not implemented.
- DGII production connection is not implemented.
- Digital signing is not implemented.
- Full XML schema compliance / instance validation is not implemented.
- OCR, AI, payments, and a custom frontend are not implemented yet.
