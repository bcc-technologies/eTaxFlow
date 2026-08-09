# Checkpoint 013 — Demo Facet Hardening Verified

## Verification date

2026-08-09

## Result

Phase 013 is verified complete on branch `revamp/dgii-vault-mvp`.

The facet-safe seeded path was exercised with:

- `seed_bcc`
- `allocate_demo_encf --xsd-facet-demo --allow-demo --apply`
- `prepare_signing_placeholder --apply`
- `validate_tipo31_unsigned_draft --allow-demo-encf --json`

Observed grouped result:

| Group | Count | Interpretation |
|---|---:|---|
| `signature_missing_expected` | 1 | Expected because the draft is intentionally unsigned. |
| `demo_facet_mismatch` | 0 | Synthetic issuer/RNC/eNCF values match the local XSD facets. |
| `local_xsd_stub_required` | 1 | Informational local-source limitation; an experimental in-memory type stub was used. |
| `unknown` | 0 | No unclassified validation errors. |

## Safety assertions

- `compliance_status`: `NOT_DGII_COMPLIANT`
- `dgii_submission_allowed`: `false`
- `signature_present`: `false`
- No DGII calls were made.
- No TrackId was created.
- No Signature or XMLDSig material was generated.
- The synthetic facet-safe eNCF remains non-authorized demo data.

## Verification commands

```text
.venv/bin/python manage.py seed_bcc
.venv/bin/python manage.py allocate_demo_encf --internal-code BCC-AR-2026-000001 --xsd-facet-demo --allow-demo --apply
.venv/bin/python manage.py prepare_signing_placeholder --internal-code BCC-AR-2026-000001 --apply --note "Local placeholder only; no real digital signature"
.venv/bin/python manage.py validate_tipo31_unsigned_draft --internal-code BCC-AR-2026-000001 --allow-demo-encf --json
.venv/bin/python -m pytest -q
```

Pytest result: **175 passed**.

Generated files under `media/` were left uncommitted.
