# Tipo 31 Printed Representation Draft Notes

## Status

Phase 018 provides a deterministic, local PDF representation for an internal
Tipo 31 invoice draft. It is stored as a generated `Document` linked to the
invoice, but it is not an approved fiscal representation and is not DGII
certification evidence.

## Implementation

`ecf.printed.tipo31_printed_draft` uses a small standard-library PDF writer and
the standard Helvetica PDF font. No new PDF dependency was available or
required. The output contains source-backed invoice and line fields:

- internal invoice code and Tipo e-CF code;
- local/demo eNCF, visibly labeled synthetic/local when applicable;
- issue/due dates and currency;
- issuer/customer names, RNC/ID values, and addresses;
- line descriptions, quantities, prices, taxes, and totals; and
- local status and non-production warnings.

The byte output is deterministic for unchanged source data. Repeated
generation reuses the linked `Document` when the filename and SHA-256 match.
The `Document` stores file size, MIME type, SHA-256, issuer, customer, invoice,
and `STORED` status. Generation writes an audit event with the same metadata.

## Deliberate omissions

No QR code, security code, DGII approval mark, TrackId, certificate, Signature,
XMLDSig, or production authorization is emitted. The PDF states that the QR or
security code is omitted because no source-backed value is available. Signature
is explicitly `NOT_IMPLEMENTED`.

## Safety boundary

- Representation status: `NON_PRODUCTION_DRAFT`
- Compliance status: `NOT_DGII_COMPLIANT`
- DGII approval claim: `false`
- DGII submission allowed: `false`
- DGII calls: none
- TrackId: none

The command is local-only and does not mutate invoice approval or issuance
state.
