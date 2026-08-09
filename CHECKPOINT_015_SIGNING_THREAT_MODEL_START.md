# Checkpoint 015 — Signing Threat Model and Key-Management Design Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 014 commit: `85baa3f`
- Django system check: passed
- Existing generated files under `media/` remain untracked and excluded from commits

## Scope

Document signing architecture and threat model, then add disabled/test-safe
settings placeholders. This phase must not implement XMLDSig, persist keys or
certificates, handle passphrases, or alter the unsigned draft behavior.

## Safety boundary

Production signing remains blocked. All defaults must be disabled and safe for
local tests. No DGII calls, submission, TrackId, certificates, private keys, or
real credentials are permitted.
