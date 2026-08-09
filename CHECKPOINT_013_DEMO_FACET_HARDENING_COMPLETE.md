# Checkpoint 013 — Demo Facet Hardening Complete

## Branch

`revamp/dgii-vault-mvp`

## Migrations

`fiscal/migrations/0005_encf_source_xsd_facet_demo.py` — adds `XSD_FACET_DEMO` to `ENCFSequenceRange.source` choices.

Subsequent `makemigrations`: **No changes detected**.

## Files changed / added

### Added
- `CHECKPOINT_013_DEMO_FACET_HARDENING_START.md`
- `CHECKPOINT_013_DEMO_FACET_HARDENING_COMPLETE.md`
- `core/demo_profiles.py`
- `docs/dgii/mapping/TIPO31_XSD_FACET_NOTES.md`
- `ecf/dgii/xsd/facets.py`
- `fiscal/migrations/0005_encf_source_xsd_facet_demo.py`
- `tests/test_demo_facet_hardening.py`

### Updated
- `core/management/commands/seed_bcc.py`
- `core/seed_demo.py`
- `ecf/dgii/xsd/tipo31_unsigned_validation.py`
- `ecf/management/commands/validate_tipo31_unsigned_draft.py`
- `fiscal/management/commands/allocate_demo_encf.py`
- `fiscal/models.py`
- `fiscal/services/encf_sequences.py`
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`
- Tests updated to use `DEMO_ISSUER_RNC` (`131000001`):
  - `ecf/tests.py`
  - `tests/test_dgii_mapping.py`
  - `tests/test_document_link.py`
  - `tests/test_invoice_workflow.py`
  - `tests/test_merge_duplicate_contacts.py`
  - `tests/test_models.py`
  - `tests/test_seed_demo_cleanup.py`

## Facet constraints extracted

From `docs/dgii/sources/e-CF_31_v1.0.xsd`:

| field | XSD type | pattern | length |
|---|---|---|---|
| `eNCF` | `eNCFValidationType` | `([a-z0-9A-Z]{13})` | min/max 13 |
| `RNCEmisor` / `RNCComprador` | `RNCValidationType` | `[0-9]{11}\|[0-9]{9}` | 9 or 11 digits |

## Demo values changed

| item | before | after |
|---|---|---|
| Issuer RNC (owned demo) | `1310000000` (10 digits) | `131000001` (synthetic 9 digits) |
| Customer RNC | `123456789` | unchanged (already facet-safe) |
| Supplier RNC | `987654321` | unchanged (already facet-safe) |
| Classic demo eNCF | `DEMO-E31-######` | retained as default |
| Facet-safe eNCF | n/a | `E31` + 10 digits, e.g. `E319000000001` via `XSD_FACET_DEMO` |

All values remain synthetic / non-authorized. Non-demo orgs with invalid RNCs are warned and left unchanged.

## eNCF facet-safe strategy

- Keep `MANUAL_DEMO` / `DEMO-E31-` as default allocation.
- Seed separate active range: prefix `E31`, source `XSD_FACET_DEMO`, `environment=DEV`, `is_authorized_by_dgii=False`.
- Allocate only with:
  `allocate_demo_encf --xsd-facet-demo --allow-demo --apply`
- Mapping still emits `DEMO_OR_UNAUTHORIZED_ENCF` for pattern-compatible facet demos.

## Validation errors before / after

### Before (Phase 012 / pre-hardening)
- `error_count`: **4**
- Avoidable: issuer RNC pattern + DEMO-E31 eNCF length/pattern
- Intentional: Signature / missing `xs:any`
- Local stub: experimental type repair for `IndicadorServicioTodoIncluidoType`

### After (facet-safe seed + `--xsd-facet-demo` allocation)
- `error_count` / `total_error_count`: **1**
- `intentional_unsigned_error_count`: **1**
- `avoidable_demo_facet_error_count`: **0**
- `local_xsd_stub_error_count`: **1** (informational stub note; schema repair applied)
- `structural_mismatch_count`: **4**
- `unknown_error_count`: **0**
- `compliance_status`: `NOT_DGII_COMPLIANT`
- `signature_present`: `false`
- `schema_mode`: `LOCAL_XSD_WITH_EXPERIMENTAL_TYPE_STUB`

## Grouped error counts (after)

| group | count |
|---|---|
| `signature_missing_expected` | 1 |
| `demo_facet_mismatch` | 0 |
| `local_xsd_stub_required` | 1 (informational) |
| `structural_mismatch` | 0 (in XSD error groups; separate structural list still has expected unsigned notes) |
| `unknown` | 0 |

## Final pytest result

**175 passed**

## Known limitations

- Signature / XMLDSig still intentionally omitted.
- Pattern-compatible demo eNCF is still not DGII-authorized.
- Local XSD still requires experimental in-memory stub (type name whitespace defect).
- Seed migrates only clearly owned legacy demo issuer rows; dirty non-demo data is warned, not mutated.
- Classic `DEMO-E31-` path still produces avoidable facet mismatches by design.

## Exact next recommended task

**Phase 014 — unsigned draft structural tightening against local XSD beyond facets** (or design a real signing architecture spike): inventory remaining non-facet structural gaps for Tipo 31 unsigned `ECF` (optional/conditional elements, totals, dates, namespaces), still without XMLDSig, certificates, DGII calls, or compliance claims. Prefer a focused structure/catalog pass that keeps `NOT_DGII_COMPLIANT` and Signature intentionally missing.
