# Checkpoint 035 — Inbound Reporting Export Lab Complete

## Branch / commit base

- Branch: `revamp/dgii-vault-mvp`
- Base: `b379f25` (Phase 034)

## Files changed (summary)

### New
- `CHECKPOINT_035_INBOUND_REPORTING_EXPORT_LAB_START.md`
- `CHECKPOINT_035_INBOUND_REPORTING_EXPORT_LAB_COMPLETE.md`
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_REPORTING_EXPORT_LAB.md`
- `ecf/dgii/inbound_reporting_lab.py`
- `ecf/dgii/inbound_reporting_lab_readiness.py`
- `ecf/management/commands/dgii_inbound_reporting_lab.py`
- `tests/test_dgii_inbound_reporting_lab.py`
- `runtime/dgii_lab_reports/.gitkeep`
- `ecf/migrations/0007_rename_inbound_lab_index_names_under_30.py`

### Updated
- Lab report builders: XML / schema / signature / persistence / workflow / audit / security
- `ecf/dgii/receiver.py`, `dgii_receiver_contract`, `dgii_readiness_report`
- README + DGII lab/security/endpoint/readiness docs
- `.gitignore` (`runtime/dgii_lab_reports/*`)
- `tests/test_dgii_readiness_report.py` (Phase 035 blockers)

## Migrations

`0007_rename_inbound_lab_index_names_under_30` — renames lab workflow/audit indexes to Django auto names ≤30 chars (fixes `models.E034`). No schema/model fields added. Phase 035 itself is report-only.

## Reporting lab

- Command: `dgii_inbound_reporting_lab`
- Flags: `--json`, `--summary-only`, `--export-json`, `--export-csv`, `--export-markdown`, `--export-bundle`, `--output-dir`
- Bundle writes under `runtime/dgii_lab_reports/`:
  - `inbound_lab_report.json`
  - `inbound_lab_summary.csv`
  - `inbound_lab_summary.md`
  - `manifest.json`
- Path traversal rejected
- **No raw XML** (`raw_xml_text` absent from exports)
- No DB writes, no DGII calls, no TrackId

## Private key safety

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` → only `.conda/.../api-ms-win-crt-private-*.dll` false positives. No keys added.

## Receiver / readiness

- Receiver: `inbound_reporting_lab_available=true`, `production_dashboard_ready=false`, `raw_xml_export_enabled=false`, metadata-only exports
- Readiness: **BLOCKED** / **NOT_DGII_COMPLIANT** / `dgii_submission_allowed=false`
- Phase 035 blockers present (7)
- Blocker count observed: **109** (was 102 after Phase 034)

## Final pytest

**415 passed** (baseline 396 + Phase 035 coverage)

## Remaining

Public `/fe/...` still 503 DISABLED. No certification claim. `production_security_ready=false`.

## Next recommended phase

**Phase 036 — Staging deployment evidence collector lab**
