# Checkpoint 018 — Non-Production Printed Representation Complete

## Result

Phase 018 is complete on branch `revamp/dgii-vault-mvp`.

## Delivered

- `ecf/printed/tipo31_printed_draft.py`
- `ecf/management/commands/generate_tipo31_printed_draft.py`
- `docs/dgii/printed/PRINTED_REPRESENTATION_NOTES.md`
- `tests/test_tipo31_printed_draft.py`

## Verified behavior

- Generates a deterministic PDF from source-backed invoice/line fields.
- Saves it as a `Document` with `document_kind=PDF`, generated source, linked
  invoice/issuer/customer, MIME type, file size, and SHA-256.
- Creates a `tipo31_printed_draft_generated` audit event.
- Reuses the byte-identical document on repeated generation.
- Marks output `NON_PRODUCTION_DRAFT` and `NOT_DGII_COMPLIANT`.
- Omits QR/security values because no source-backed value exists.
- Does not claim approval, sign, call DGII, or create TrackId.

## Verification

- `makemigrations`: no changes detected
- `migrate`: no migrations to apply
- `manage.py check`: passed
- Focused printed-draft tests: **3 passed**
- Full pytest: **192 passed**
- Management command invocation: passed; generated 1,894-byte local PDF
