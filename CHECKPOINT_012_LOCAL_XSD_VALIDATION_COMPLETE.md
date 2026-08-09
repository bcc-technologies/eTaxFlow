# Checkpoint 012 — Local XSD Validation Complete

## Files changed

- `CHECKPOINT_012_LOCAL_XSD_VALIDATION_START.md` (new)
- `CHECKPOINT_012_LOCAL_XSD_VALIDATION_COMPLETE.md` (new)
- `requirements.txt` (added `lxml>=5.0,<7.0`)
- `ecf/dgii/xsd/validation.py` (new)
- `ecf/dgii/xsd/tipo31_unsigned_validation.py` (new)
- `ecf/dgii/xsd/__init__.py`
- `ecf/dgii/xml_draft/tipo_ecf_31_unsigned.py` (diagnostics flags)
- `ecf/management/commands/validate_tipo31_unsigned_draft.py` (new)
- `tests/test_tipo31_xsd_validation.py` (new)
- `docs/dgii/validation_reports/README.md` (new)
- `docs/dgii/validation_reports/.gitkeep` (new)
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`
- `.gitignore`

## Migrations created

No changes detected

## Validator dependency / engine

- Added `lxml>=5.0,<7.0` because Python stdlib cannot validate XML against XSD
- Engine: **`lxml`**
- Offline only (`no_network=True`); no remote schema fetch

## XSD path used

`docs/dgii/sources/e-CF_31_v1.0.xsd`

## Validation result

For seeded invoice after allocate + placeholder + unsigned draft:

- `is_valid`: **false**
- `expected_validity`: **false**
- `expected_invalid_unsigned_draft`: **true**
- `compliance_status`: **NOT_DGII_COMPLIANT**
- `schema_mode`: `LOCAL_XSD_WITH_EXPERIMENTAL_TYPE_STUB`
- `schema_repair_applied`: **true** (local XSD references undefined `IndicadorServicioTodoIncluidoType`)
- `error_count`: **4**

## Expected failure reasons

1. Signature missing / unsigned draft (required XSD `xs:any` / Formato Signature omitted)
2. Demo/non-authorized eNCF facet mismatches (length/pattern)
3. Local XSD compile requires experimental type stub

Also observed instance facet error: demo issuer RNC length vs `[0-9]{11}|[0-9]{9}`.

## Number of validation errors

**4** (for BCC-AR-2026-000001 verification run)

## Report writing

Works: `--write-report /tmp/tipo31_unsigned_validation.md` created Markdown successfully. Generated reports under `docs/dgii/validation_reports/` are gitignored; README is tracked.

## Command behavior

`python manage.py validate_tipo31_unsigned_draft`

- Builds unsigned draft in memory (no Document/ECFDocument mutation from validation itself)
- Human report by default; `--json` for JSON; `--write-report` for Markdown
- Exits successfully for expected invalid unsigned draft
- Does not sign/submit/create TrackId

## Final pytest result

**161 passed**

## Known limitations

- Local XSD is not fully self-contained (missing type definition)
- Experimental type stub is not official DGII schema
- Unsigned draft remains invalid by design (no Signature)
- Demo eNCF / some seed identity values may fail XSD facets
- Not certification evidence; not DGII compliance

## Exact next recommended task

**Phase 013 — seed/demo data facet hardening for local XSD feedback:** adjust non-production seed values (e.g. issuer RNC length) and/or document remaining facet mismatches so local validation noise is minimized while Signature remains intentionally missing and status stays **NOT_DGII_COMPLIANT**.
