# Test-only signing fixture policy

This directory intentionally contains no key, certificate, passphrase, or
signed XML material. Phase 016 generates ephemeral RSA test material through
the local OpenSSL CLI inside a temporary directory and removes it before the
test returns.

Any future fixture must be synthetic, explicitly marked `TEST_ONLY`, ignored
from version control if it is generated, and covered by a test that prevents
private-key/certificate material from being committed. Production material is
never permitted here.
