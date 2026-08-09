# Tipo 31 Unsigned Draft — Structural Tightening Notes

## Scope and safety

This is an offline comparison of the unsigned Tipo e-CF 31 draft against the
local `docs/dgii/sources/e-CF_31_v1.0.xsd`. It is not DGII certification
evidence. The comparison does not call DGII, create TrackId values, sign XML,
or authorize demo eNCF values.

## Comparison result

For the facet-safe synthetic demo invoice:

| Check | Result |
|---|---|
| XSD root | `ECF` |
| Draft root | `ECF` |
| XSD body sequence | `Encabezado`, `DetallesItems`, `Subtotales`, `DescuentosORecargos`, `Paginacion`, `InformacionReferencia`, `FechaHoraFirma` |
| Draft body sequence | `Encabezado`, `DetallesItems`, `FechaHoraFirma` |
| Required body elements missing | None |
| Unexpected body elements | None |
| Body order mismatches | None |
| Optional elements omitted | `Subtotales`, `DescuentosORecargos`, `Paginacion`, `InformacionReferencia` |
| Known omitted signing particle | Required `xs:any`, represented as `Signature` in diagnostics |
| `unsigned_body_structurally_aligned_except_signature` | `true` |

The four omitted body elements are source-backed optional XSD particles
(`minOccurs=0`), so their omission is allowed and is not a structural defect.
`FechaHoraFirma` is emitted in the source-backed position. The required final
`xs:any` particle remains intentionally absent because XMLDSig is not
implemented.

## Error classification

Validation output now distinguishes:

- `signature_missing_expected`
- `demo_facet_mismatch`
- `local_xsd_stub_required`
- `structural_element_order_mismatch`
- `structural_missing_element`
- `structural_unexpected_element`
- `structural_type_or_value_mismatch`
- `unknown`

The structural categories are populated from both local XSD messages and the
source-backed top-level comparison. Demo authorization and the local XSD type
stub are reported separately; neither is mislabeled as a body-structure
mismatch.

## Verified counts

- `structural_mismatch_count`: `1` (the expected Signature omission)
- `non_signature_structural_mismatch_count`: `0`
- `signature_missing_expected_count`: `1`
- `facet_mismatch_count`: `0`
- `xsd_stub_informational_count`: `1`
- `unknown_error_count`: `0`
- `compliance_status`: `NOT_DGII_COMPLIANT`
- `dgii_submission_allowed`: `false`

## Explicit non-claims

- No Signature or XMLDSig was generated.
- No production e-CF behavior was implemented.
- This result does not establish DGII compliance or certification readiness.
