# Checkpoint 017 — Signed Sandbox Local XSD Validation Complete

## Result

Phase 017 is complete on branch `revamp/dgii-vault-mvp`.

## Delivered

- `ecf/dgii/xsd/tipo31_signed_sandbox_validation.py`
- `ecf/management/commands/validate_tipo31_signed_sandbox.py`
- `docs/dgii/validation_reports/SIGNED_SANDBOX_VALIDATION_NOTES.md`
- `tests/test_signed_sandbox_validation.py`

## Verified behavior

- Builds the unsigned Tipo 31 draft in memory.
- Applies sandbox signing only with explicit `--test-only`.
- Verifies the synthetic Signature locally.
- Validates the signed artifact against the local XSD offline.
- Reports `xsd_valid=true`, `signed_sandbox_valid=true`,
  `TEST_ONLY_SIGNATURE`, zero remaining errors, and schema-stub limitations.
- Remains `NOT_DGII_COMPLIANT`; submission is false; TrackId is null; no DGII
  call occurs.
- Does not persist a signed document or production signing material.

## Verification

- `makemigrations`: no changes detected
- `migrate`: no migrations to apply
- `manage.py check`: passed
- Full pytest: **189 passed**
- Human and JSON management-command invocations: passed
