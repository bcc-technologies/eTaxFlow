# XMLDSig Sandbox Notes

## Dependency decision

The project already provides `lxml` for offline XML/XSD work, but it does not
provide `cryptography`, `signxml`, or `xmlsec`. Phase 016 therefore adds no
Python signing dependency. The sandbox uses the system OpenSSL CLI only for
ephemeral test material and RSA-SHA256 operations. This is a test harness
choice, not a production signer recommendation.

The OpenSSL invocation is argument-array based, runs with a short timeout,
captures output without logging it, and uses a `TemporaryDirectory` for the
key, self-signed test certificate, canonicalized `SignedInfo`, and signature
bytes. The temporary directory is removed before the function returns.

## Implemented sandbox behavior

`ecf.services.signing_sandbox` provides:

- `sign_xml_sandbox(xml_bytes, test_only=True)`;
- `verify_xml_sandbox_signature(xml_bytes, test_only=True)`; and
- `sandbox_signature_diagnostics(xml_bytes)`.

The prototype creates an enveloped XMLDSig with exclusive canonicalization,
RSA-SHA256, SHA-256 document digest, and an embedded synthetic self-signed
certificate. Verification checks the enveloped digest and RSA signature
locally. The certificate is test-only and is not a DGII certificate.

## Safety boundary

- `test_only=True` must be explicit for this API.
- `test_only=False` fails closed.
- `attempt_real_signing` remains blocked.
- Signed output is labeled `TEST_ONLY_SIGNATURE` in diagnostics.
- Signed output remains `NOT_DGII_COMPLIANT` and `dgii_submission_allowed=false`.
- No TrackId, DGII call, production certificate, or private key is created.
- The existing unsigned draft builder remains unsigned; sandbox signing is a
  separate test operation.

This prototype is not certification evidence and must not be used as a live
DGII integration.
