"""Test-only XMLDSig helper (NON_PRODUCTION_TEST_ONLY).

Phase 030 does not generate valid XMLDSig documents. Cryptographic signing would
require a new heavy dependency (e.g. signxml) and is out of scope.

This helper documents that tests must assert PLACEHOLDER_ONLY /
VERIFICATION_NOT_IMPLEMENTED rather than inventing production-valid signatures.
Private keys must never be written to disk or committed.
"""

NON_PRODUCTION_TEST_ONLY = True
XMLDSIG_GENERATION_IMPLEMENTED = False
XMLDSIG_VERIFICATION_IMPLEMENTED = False


def skip_reason() -> str:
    return (
        "Valid test-only XMLDSig generation/verification is NOT_IMPLEMENTED; "
        "Phase 030 inspects Signature nodes only and classifies placeholders honestly."
    )
