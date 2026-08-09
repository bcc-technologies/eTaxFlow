# Checkpoint 009 — Signing Placeholder Complete

## Files changed

- `CHECKPOINT_009_SIGNING_PLACEHOLDER_START.md` (new)
- `CHECKPOINT_009_SIGNING_PLACEHOLDER_COMPLETE.md` (new)
- `ecf/models.py`
- `ecf/admin.py`
- `ecf/migrations/0003_signing_placeholder_fields.py` (new)
- `ecf/services/signing_placeholder.py` (new)
- `ecf/management/commands/prepare_signing_placeholder.py` (new)
- `ecf/dgii/mapping.py`
- `ecf/dgii/types.py`
- `ecf/dgii/field_catalogs/tipo_ecf_31.py`
- `invoicing/admin.py`
- `core/management/commands/seed_bcc.py`
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`
- `tests/test_signing_placeholder.py` (new)

## Migrations created

- `ecf/migrations/0003_signing_placeholder_fields.py`

## Signing placeholder model fields

On `ECFDocument`:
- `signing_status` (default `UNSIGNED`)
- `signing_mode` (default `NONE`)
- `signature_datetime` (nullable placeholder FechaHoraFirma)
- `signature_digest_algorithm` / `signature_method` / `signature_reference_uri` (nullable metadata stubs)
- `signature_placeholder_note`
- `signed_by` (nullable User FK)
- `signing_attempted_at` / `signing_completed_at`

No private keys, certificates, passphrase, or XMLDSig payload fields.

## Service behavior

`prepare_signing_placeholder(invoice, actor=None, note=None)`:
- Requires `official_encf`, `sequence_expiration_date`, `fiscal_document_type_ref`
- Creates/updates `ECFDocument` to `SIGNING_PLACEHOLDER` / `PLACEHOLDER_ONLY`
- Sets `signature_datetime` and `signing_attempted_at`
- Leaves `signing_completed_at`, `xml_signed_file`, `dgii_track_id` empty
- Writes AuditEvent `signing_placeholder_prepared`

`attempt_real_signing(...)` raises `NotImplementedError` with an explicit no-keys/no-certificates message.

## Dry-run result

- Validates prerequisites
- Reports would-be `SIGNING_PLACEHOLDER` / `PLACEHOLDER_ONLY`
- No mutation

## Apply result

- ECFDocument id prepared with `signing_status=SIGNING_PLACEHOLDER`
- `signature_datetime` set
- `xml_signed_file=False`, `dgii_track_id=None`

## Mapping result after placeholder

- Status: `READY_FOR_FUTURE_DRAFT`
- Available field count: **21**
- Missing required: **1** — `Signature`
- Warnings: `DEMO_OR_UNAUTHORIZED_ENCF`, `SIGNING_PLACEHOLDER_ONLY`
- Compliance: **NOT_DGII_COMPLIANT**

## Remaining missing required fields

1. `Signature`

## Final pytest result

**104 passed**

## Known limitations

- FechaHoraFirma placeholder is not a real digital signature timestamp.
- No XMLDSig, certificates, or private keys.
- Demo eNCF remains non-authorized.
- No DGII submission / TrackId.
- No production e-CF XML generation.
- `SIGNED` status is reserved and not set by this phase.

## Exact next recommended task

Design a **non-production internal e-CF XML structure preview** for Tipo 31 that emits an explicitly marked `NOT_DGII_COMPLIANT` draft XML from mapped invoice/ECFDocument fields — still without XMLDSig, certificates, TrackId, or DGII submission.
