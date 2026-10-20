# Checkpoint 034 — Inbound Security Controls Policy Review Lab Complete

## Branch

`revamp/dgii-vault-mvp`

## Base commit

`49b920d` — Add non-production inbound audit retention lab

## Files changed

- `CHECKPOINT_034_INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB_START.md` (new)
- `CHECKPOINT_034_INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB_COMPLETE.md` (new)
- `docs/dgii/security/INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB.md` (new)
- `ecf/dgii/inbound_security_policy_lab.py` (new)
- `ecf/dgii/inbound_security_policy_lab_readiness.py` (new)
- `ecf/management/commands/dgii_inbound_security_policy_lab.py` (new)
- `tests/test_dgii_inbound_security_policy_lab.py` (new)
- `runtime/dgii_security_reports/.gitkeep` (new)
- Updates: settings placeholders, receiver contract, readiness report, inbound XML/schema/signature/persistence/workflow/audit labs, README and related docs, `.gitignore`

## Migrations created

**No changes detected** for Phase 034 (no new models).  
Note: `makemigrations --check` may propose cosmetic index renames from prior lab models; those renames were **not** applied in this phase.

## Security policy documentation created

`docs/dgii/security/INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB.md`

## Security control catalog summary

27 controls evaluated. Example outcomes under default settings:

- **PASS:** endpoint disabled-by-default, 503 stubs, no-parse/no-persist/no-TrackId while disabled, safe lab parsers, raw XML storage default off, destructive retention disabled, DGII submission disabled
- **NOT_IMPLEMENTED / blockers:** body size enforcement, content-type enforcement, rate limiting, production signature verify, trust chain, revocation
- **MANUAL_REVIEW:** logging redaction, secrets, environment separation, DNS/TLS, Phase 024 gate, security owner / incident response
- **Policy decision:** `SECURITY_POLICY_BLOCKED`
- Placeholders (`ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES`, etc.) reported as **CONFIGURED_PLACEHOLDER**, not **ENFORCED**

## Command summary

`python manage.py dgii_inbound_security_policy_lab`

- `--json`
- `--summary-only`
- `--export-report`
- `--export-path` (must stay under `runtime/dgii_security_reports/`)

Report-only: **no DB writes**, no endpoint enablement, no DGII, no TrackId.

## Export report behavior

`--export-report` writes metadata-only JSON under `runtime/dgii_security_reports/`. Path traversal outside that directory is rejected. No raw XML.

## Disabled endpoint guarantee

Public `/fe/...` stubs remain **503 DISABLED**. Views do not import `inbound_security_policy_lab`. No XML parse, no DB write, no TrackId.

## Security blockers (Phase 034 readiness)

- `inbound_security_policy_lab_only`
- `public_endpoint_security_controls_not_enforced`
- `body_size_limit_not_enforced`
- `content_type_allowlist_not_enforced`
- `rate_limiting_not_implemented`
- `logging_redaction_policy_not_approved`
- `certificate_trust_chain_not_implemented`
- `revocation_check_not_implemented`
- `security_owner_review_not_completed`
- `incident_response_policy_not_approved`
- `environment_separation_not_verified`
- `dns_tls_not_verified_for_public_receiver`
- `phase_024_human_gate_not_signed_off`

## Private key safety check result

`git ls-files | grep -Ei 'private|privkey|key.pem|\.p12|\.pfx|\.key$'` matched only pre-existing `.conda/.../api-ms-win-crt-private-l1-1-0.dll` (Windows CRT DLL name). **False positive.** No private key files added.

## Receiver contract update summary

- `inbound_security_policy_lab_available`: true
- `security_policy_scope`: NON_PRODUCTION_LAB_ONLY
- `security_policy_command`: dgii_inbound_security_policy_lab
- `security_policy_decision`: SECURITY_POLICY_BLOCKED
- `production_security_ready`: false
- `public_endpoint_security_controls_enforced`: false
- `body_size_limit_enforced` / `content_type_allowlist_enforced` / `rate_limiting_enforced`: false
- `logging_redaction_approved` / `trust_chain_validation_ready` / `revocation_check_ready`: false

## Readiness status

- `overall_status`: **BLOCKED**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `dgii_submission_allowed`: **false**
- `production_security_ready`: **false**
- `production_signature_ready`: **false**
- `dgii_call_made`: **false**
- `track_id`: **null**
- Blockers: **102** (13 new Phase 034 security policy blockers; was 89)

## Final pytest result

**396 passed** (was 374 at Phase 034 start).

## Remaining blockers

Prior Phase 024–033 blockers plus Phase 034 security policy blockers above. Public processing remains blocked.

## Exact next recommended phase

**Phase 035 — Security-owner sign-off / staging rehearsal checklist** — human security review of Phase 034 catalog; still no public endpoints, no DGII live, no TrackId unless explicitly authorized later.
