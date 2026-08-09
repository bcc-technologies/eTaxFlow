# Mock DGII Service Contract Notes

## Purpose

Phase 019 defines transport-neutral contracts for a future DGII integration:

- semilla/token authentication;
- e-CF reception;
- result/status consultation;
- commercial approval/rejection; and
- receipt acknowledgment.

The contracts model request/result shapes only. They do not claim that the
application is certified or authorized to call DGII.

## Mock-only behavior

`MockDGIITransport` returns deterministic synthetic values such as
`MOCK-TOKEN-000001` and `MOCK-TRACK-000001`. It records in-memory call counts,
supports configured statuses, and never imports an HTTP client or opens a
socket. Mock TrackIds are not DGII TrackIds and are not persisted by this
phase.

`LiveDGIITransport` raises `NotImplementedError` during construction. Any
future live transport requires a separate explicit implementation and review.

## Safe defaults

The Django settings defaults are:

- `DGII_ENVIRONMENT=MOCK`;
- software name/version/type = `eTaxFlow` / `MVP` / `INTERNAL`;
- blank reception, commercial-approval, and authentication URLs; and
- `DGII_LIVE_TRANSPORT_ENABLED=false`.

No credentials, production URLs, or live network behavior are included.
