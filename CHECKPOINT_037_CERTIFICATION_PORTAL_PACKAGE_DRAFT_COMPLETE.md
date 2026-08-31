# Checkpoint 037 — Certification Portal Package Draft Complete

## Branch / commit base

- Branch: `revamp/dgii-vault-mvp`
- Base: `6710797` (Phase 036)

## Files changed (summary)

### New
- `CHECKPOINT_037_CERTIFICATION_PORTAL_PACKAGE_DRAFT_START.md`
- `CHECKPOINT_037_CERTIFICATION_PORTAL_PACKAGE_DRAFT_COMPLETE.md`
- `docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md`
- `ecf/dgii/certification_package_lab.py`
- `ecf/dgii/certification_package_lab_readiness.py`
- `ecf/management/commands/dgii_certification_package_lab.py`
- `tests/test_dgii_certification_package_lab.py`
- `runtime/dgii_certification_package_drafts/.gitkeep`

### Updated
- `ecf/dgii/endpoints.py`, `ecf/dgii/receiver.py`, readiness report
- All inbound labs + staging evidence + reporting
- README and related DGII/deployment docs
- `.gitignore`
- `tests/test_dgii_readiness_report.py`

## Migrations

**No changes detected**

## Package module / command

- Defaults: `software_type=PROPIO`, `software_name=eTaxFlow`, `PACKAGE_BLOCKED`, `submission_allowed=false`
- Planned paths for recepción / aprobación / autenticación
- Export: JSON + Markdown + manifest under `runtime/dgii_certification_package_drafts/`
- No portal upload, no signing, no network, no DGII, no TrackId

## Private key safety

Only `.conda/.../api-ms-win-crt-private-*.dll` false positives. No keys added.

## Endpoint / receiver / readiness

- Endpoint & receiver: `certification_package_lab_available=true`, `portal_submission_allowed=false`
- Readiness: **BLOCKED** / **NOT_DGII_COMPLIANT** / `dgii_submission_allowed=false` / `portal_submission_allowed=false`
- Phase 037 blockers present
- Blocker count observed: **133**

## Final pytest

**441 passed** (baseline 428 + Phase 037 coverage)

## Next recommended phase

**Phase 038 — Final non-production pre-cert go/no-go review**
