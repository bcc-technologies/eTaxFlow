# Local DGII Certification Harness Notes

## Purpose and provenance

The Phase 020 harness is a local preparation tool. It accepts only fixtures
marked `synthetic` or `sanitized`, requires a provenance disclaimer, and does
not invent official DGII certification cases. The committed fixture is
synthetic and explicitly not official, not DGII-compliant, and not
certification evidence.

## Flow

1. Load the marked JSON fixture.
2. Map each row to local `Invoice` and `InvoiceLine` objects using source-row
   values and internal catalog records.
3. Prepare a local signing placeholder so the existing draft prerequisites are
   explicit.
4. Run either unsigned local XSD diagnostics or the explicit sandbox-signed
   local XSD validator.
5. Produce a local pass/expected-limitation report.

The importer uses the project’s deterministic soft natural-key resolver for
contacts, so existing duplicate contacts do not cause `MultipleObjectsReturned`
and are not silently merged or deleted.

## Modes and outcomes

- `unsigned`: reports `EXPECTED_UNSIGNED_LIMITATION` because Signature remains
  intentionally absent; this is not a DGII failure classification.
- `sandbox-signed`: reports `PASS` only when the test-only Signature verifies
  and local XSD validation succeeds. The result remains
  `NOT_DGII_COMPLIANT`.

The command requires `--no-submit`. The report always contains
`submitted=false`, `dgii_call_made=false`, and an empty `track_ids` list.

## Explicit non-claims

- No official DGII certification test case was created or inferred.
- No DGII endpoint, credential, TrackId, or live network call is used.
- A local sandbox pass is not DGII certification evidence.
- The harness does not authorize production e-CF behavior.
