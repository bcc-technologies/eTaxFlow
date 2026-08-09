# Local XSD validation reports

This directory holds **local** Markdown reports produced by:

```bash
python manage.py validate_tipo31_unsigned_draft --internal-code ... --allow-demo-encf --write-report docs/dgii/validation_reports/....md
```

## Rules

- Reports are local laboratory artifacts only.
- Unsigned Tipo 31 drafts are **expected to fail** local XSD validation.
- Missing `Signature` / omitted XSD `xs:any` is expected while signing is unimplemented.
- Demo/non-authorized eNCF values remain unauthorized and may also fail XSD facets.
- The local `e-CF_31_v1.0.xsd` may require an experimental in-memory type stub to compile (`IndicadorServicioTodoIncluidoType` is referenced but not defined in the source file). That stub is **not** official DGII schema content.

## Explicit non-claims

- Reports must **not** be treated as DGII certification evidence.
- Reports must **not** be treated as DGII compliance.
- No signing, certificates, private keys, TrackId, or DGII submission occurs during validation.

Generated `*.md` reports in this folder are gitignored by default.
