# Checkpoint 036 — Staging Deployment Evidence Collector Lab Complete

## Branch / commit base

- Branch: `revamp/dgii-vault-mvp`
- Base: `f82a249` (Phase 035)

## Files changed (summary)

### New
- `CHECKPOINT_036_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB_START.md`
- `CHECKPOINT_036_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB_COMPLETE.md`
- `docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md`
- `ecf/dgii/staging_evidence_lab.py`
- `ecf/dgii/staging_evidence_lab_readiness.py`
- `ecf/management/commands/dgii_staging_evidence_lab.py`
- `tests/test_dgii_staging_evidence_lab.py`
- `runtime/dgii_staging_evidence/.gitkeep`

### Updated
- `ecf/dgii/endpoints.py`, `ecf/dgii/receiver.py`, readiness report
- All inbound lab report builders + reporting lab
- README, DNS/SSL checklist, receiver contract, readiness checklist, related lab docs
- `.gitignore`
- `tests/test_dgii_readiness_report.py`

## Migrations

**No changes detected**

## Evidence catalog

19 required manual evidence items (DNS/TLS/HTTPS, disabled routes/POST, env/DB/secrets/logging, governance / Phase 024). Default status `EVIDENCE_MISSING`.

## Command

`dgii_staging_evidence_lab` — `--json`, `--summary-only`, `--write-template`, `--template-path`, `--evidence-file`, `--export-report`, `--export-path`

- Template + report under `runtime/dgii_staging_evidence/`
- Path traversal rejected
- Default decision: `STAGING_EVIDENCE_BLOCKED`
- `network_checks_performed=false`
- No DB writes, no DGII, no TrackId

## Private key safety

Only `.conda/.../api-ms-win-crt-private-*.dll` false positives. No keys added.

## Endpoint / receiver / readiness

- Endpoint plan & receiver: `staging_evidence_lab_available=true`, `production_staging_ready=false`
- Readiness: **BLOCKED** / **NOT_DGII_COMPLIANT** / `dgii_submission_allowed=false` / `production_staging_ready=false`
- Phase 036 blockers present (12)
- Blocker count observed: **121**

## Final pytest

**428 passed** (baseline 415 + Phase 036 coverage)

## Next recommended phase

**Phase 037 — Certification portal submission package draft**
