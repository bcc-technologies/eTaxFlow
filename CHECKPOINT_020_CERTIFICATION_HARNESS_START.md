# Checkpoint 020 — Certification Test-Set Harness Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 019 commit: `1468ef5`
- Django system check: passed
- Full pytest: **197 passed**
- Generated `media/` files remain untracked and excluded from commits

## Scope

Create a local harness for synthetic or explicitly supplied sanitized test-set
rows. It may map rows to invoice objects, generate unsigned or test-only
signed XML, and run local validation. It must never invent official cases,
submit to DGII, create a real TrackId, or make a live network call.
