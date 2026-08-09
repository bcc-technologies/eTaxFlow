# Checkpoint 017 — Signed Sandbox Local XSD Validation Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 016 commit: `60dfa2f`
- Django system check: passed
- Full pytest: **186 passed**
- Generated `media/` files remain untracked and excluded from commits

## Scope

Build the existing unsigned Tipo 31 draft, apply the explicit test-only
sandbox signature, validate it offline against the local XSD, and report
signature/schema limitations. No DGII call, TrackId, production certificate,
submission, or compliance claim is permitted.
