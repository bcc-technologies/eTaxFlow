# Checkpoint 018 — Non-Production Printed Representation Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 017 commit: `ac20029`
- Django system check: passed
- Full pytest: **189 passed**
- Generated `media/` files remain untracked and excluded from commits

## Scope

Generate a local, non-production Tipo 31 printed representation PDF from
source-backed invoice fields, store it as a linked `Document`, and create an
audit event. The artifact must remain explicitly non-production and must not
claim DGII approval, QR/security-code validity, signing, submission, or
TrackId.
