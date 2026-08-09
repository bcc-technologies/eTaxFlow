# Checkpoint 016 — XMLDSig Sandbox Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 015 commit: `af1d091`
- Django system check: passed
- Full pytest: **181 passed**
- Generated `media/` files remain untracked and excluded from commits

## Scope

Prototype local XMLDSig only with ephemeral test-only key/certificate material.
The unsigned draft remains unchanged, production signing remains blocked, and
no key files, passphrases, certificates, signed artifacts, DGII calls, or
TrackId values may be committed or submitted.
