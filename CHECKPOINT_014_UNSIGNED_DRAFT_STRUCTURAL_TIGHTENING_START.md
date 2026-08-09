# Checkpoint 014 — Unsigned Draft Structural Tightening Start

## Baseline

- Branch: `revamp/dgii-vault-mvp`
- Phase 013 commit: `3eae78f`
- Django system check: passed
- Existing worktree changes: generated untracked files under `media/`; excluded from phase commits

## Scope

Compare the unsigned Tipo 31 draft body with the local `e-CF_31_v1.0.xsd` structure, classify structural differences separately from expected Signature omission, and improve the validation report without adding Signature, XMLDSig, non-XSD attributes, or DGII behavior.

## Safety boundary

This phase is local/offline only. It will not call DGII, create TrackId values, generate Signature/XMLDSig, or change `NOT_DGII_COMPLIANT` behavior.
