# Checkpoint 005 — DGII Schema Mapping Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**61 passed**

## seed_bcc result

```
Demo BCC data seeded.
Seeded invoice: BCC-AR-2026-000001 (lines=2, marker=SEEDED_BCC_DEMO_INVOICE)
Contacts used: client_pk=1, supplier_pk=2
```

No duplicate-contact warning.

## Duplicate diagnosis result

```
No duplicate seed records detected
```

## Current eTaxFlow XML / internal draft status

- Internal XML draft layer (Phase 004) is complete.
- `generate_internal_xml` produces deterministic **internal** drafts only.
- Internal drafts are explicitly **not** DGII-compliant and not signed.
- `ECFDocument` placeholder exists but is not used for official e-CF submission.
- Demo seed / cleanup / explicit contact-merge tooling is in place.

## Intended Phase 005 scope

- Official DGII document inventory (URLs / locations; local files marked missing until collected).
- Internal typed mapping structures from normalized `Invoice` data to future DGII e-CF concepts.
- Read-only mapping report + `inspect_dgii_mapping` management command.
- Fixture directory conventions for future sanitized / synthetic mapping cases.
- Tests proving mapping is report-only (no XML, Document, ECFDocument, or DGII calls).

## Non-goals

- Live DGII API calls
- Digital signing
- Certificate / private key storage
- TrackId submission or status polling
- Claiming DGII XML compliance
- Sending anything to DGII
- Production e-CF emission behavior
