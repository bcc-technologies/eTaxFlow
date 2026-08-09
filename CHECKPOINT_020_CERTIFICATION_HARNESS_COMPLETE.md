# Checkpoint 020 — Certification Test-Set Harness Complete

## Result

Phase 020 is complete on branch `revamp/dgii-vault-mvp`.

## Delivered

- `ecf/dgii/certification/test_set_importer.py`
- `ecf/dgii/certification/case_runner.py`
- `ecf/management/commands/run_dgii_certification_harness.py`
- `tests/fixtures/dgii/synthetic_certification_case.json`
- `docs/dgii/certification/CERTIFICATION_HARNESS_NOTES.md`
- `tests/test_certification_harness.py`

## Verified behavior

- Synthetic fixture imports and maps to an Invoice/InvoiceLine.
- Unsigned mode reports an expected Signature limitation.
- Sandbox-signed mode can pass local XSD/signature checks.
- Command requires `--no-submit` and produces local human/JSON reports.
- `submitted=false`, `dgii_call_made=false`, and `track_ids=[]`.
- Contact duplicate rows are resolved deterministically without deletion or
  silent merging.
- No official test cases are invented or claimed.

## Verification

- `makemigrations`: no changes detected
- `migrate`: no migrations to apply
- `manage.py check`: passed
- Focused harness tests: **4 passed**
- Full pytest: **201 passed**
- `run_dgii_certification_harness --synthetic --no-submit`: passed
