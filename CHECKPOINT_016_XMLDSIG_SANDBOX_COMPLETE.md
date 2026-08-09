# Checkpoint 016 — XMLDSig Sandbox Complete

## Result

Phase 016 is complete on branch `revamp/dgii-vault-mvp`.

## Delivered

- `ecf/services/signing_sandbox.py`
- `tests/test_signing_sandbox.py`
- `tests/fixtures/signing/README.md`
- `docs/dgii/signing/XMLDSIG_SANDBOX_NOTES.md`

## Behavior

- Explicit `test_only=True` creates an enveloped RSA-SHA256 XMLDSig using
  temporary OpenSSL-generated RSA key/certificate material.
- `verify_xml_sandbox_signature` verifies the local digest and signature.
- Temporary key, certificate, canonicalized SignedInfo, and signature files are
  removed before return.
- `test_only=False` fails closed.
- Real signing remains blocked through `attempt_real_signing`.
- Diagnostics label output `TEST_ONLY_SIGNATURE` and retain
  `NOT_DGII_COMPLIANT`; TrackId and DGII calls remain absent.
- The existing unsigned draft remains unchanged and unsigned.

## Safety assertions

- No Python signing dependency was added.
- No private key, certificate, passphrase, or signed output was committed.
- No secrets are logged or returned in diagnostics.
- No DGII call or submission occurs.

## Verification

- `makemigrations`: no changes detected
- `migrate`: no migrations to apply
- `manage.py check`: passed
- Focused sandbox tests: **5 passed**
- Full pytest: **186 passed**
