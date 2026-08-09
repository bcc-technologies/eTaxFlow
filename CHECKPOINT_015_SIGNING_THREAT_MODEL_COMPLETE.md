# Checkpoint 015 — Signing Threat Model and Key-Management Design Complete

## Result

Phase 015 is complete on branch `revamp/dgii-vault-mvp`.

## Delivered

- `docs/dgii/signing/SIGNING_ARCHITECTURE.md`
- `SECURITY_SIGNING_THREAT_MODEL.md`
- Disabled/test-safe signing settings placeholders in `etaxflow/settings.py`:
  `SIGNING_MODE`, `SIGNING_BACKEND`, `SIGNING_ENABLED`,
  `SIGNING_ALLOW_TEST_ONLY`, `SIGNING_CERT_PATH`, `SIGNING_KEY_PATH`, and
  `SIGNING_PASS_ENV_VAR`
- `tests/test_signing_security_design.py`

## Safety assertions

- Defaults are `DISABLED` / `NONE` / false / empty path references.
- No certificate, private-key, or passphrase model fields were added.
- `attempt_real_signing` remains blocked with `NotImplementedError`.
- No XMLDSig was implemented.
- No secrets, certificates, private keys, or generated reports were committed.
- `NOT_DGII_COMPLIANT` behavior remains unchanged.

## Verification

- `makemigrations`: no changes detected
- `migrate`: no migrations to apply
- `manage.py check`: passed
- Focused signing/security tests: **13 passed**
- Full pytest: **181 passed**
