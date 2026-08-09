# Checkpoint 019 — Mocked DGII Service Contracts Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 018 commit: `a1a6a2e`
- Django system check: passed
- Full pytest: **192 passed**
- Generated `media/` files remain untracked and excluded from commits

## Scope

Define local service contracts for authentication, reception, status,
commercial approval, and receipt acknowledgment. Implement only deterministic
mock transport. Any live HTTP transport must fail with `NotImplementedError`;
no DGII endpoint, credentials, TrackId, or submission is permitted.
