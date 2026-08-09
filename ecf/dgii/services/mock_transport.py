"""Deterministic DGII contract transport with no network capability."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    AuthenticationRequest,
    AuthenticationResult,
    CommercialApprovalResult,
    DGIIServiceConfiguration,
    MockTransportState,
    ReceiptAcknowledgmentResult,
    ReceptionRequest,
    ReceptionResult,
    StatusResult,
)


class MockDGIITransport:
    """Return explicit synthetic responses and never open a network socket."""

    def __init__(
        self,
        *,
        configuration: DGIIServiceConfiguration | None = None,
        state: MockTransportState | None = None,
    ):
        self.configuration = configuration or DGIIServiceConfiguration()
        self.state = state or MockTransportState()
        self.authentication_calls = 0
        self.reception_calls = 0
        self.status_calls = 0
        self.approval_calls = 0
        self.receipt_acknowledgment_calls = 0

    def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        self.authentication_calls += 1
        return AuthenticationResult(
            access_token=f"MOCK-TOKEN-{self.authentication_calls:06d}",
            mock=True,
            message="Synthetic mock token; no DGII authentication call.",
        )

    def submit_reception(self, request: ReceptionRequest) -> ReceptionResult:
        if not request.xml_bytes:
            raise ValueError("Mock reception requires non-empty XML bytes.")
        self.reception_calls += 1
        track_id = f"MOCK-TRACK-{self.state.next_track_number:06d}"
        self.state.next_track_number += 1
        self.state.statuses.setdefault(track_id, "RECEIVED_MOCK")
        return ReceptionResult(
            track_id=track_id,
            status=self.state.statuses[track_id],
            message="Synthetic mock TrackId; no DGII submission occurred.",
            mock=True,
        )

    def consult_status(self, track_id: str) -> StatusResult:
        self.status_calls += 1
        status = self.state.statuses.get(track_id, "UNKNOWN_MOCK")
        return StatusResult(
            track_id=track_id,
            status=status,
            status_message=self.state.status_messages.get(
                track_id, "Synthetic mock status; no DGII consultation occurred."
            ),
            mock=True,
        )

    def commercial_approval(
        self, track_id: str, *, approved: bool, reason: str = ""
    ) -> CommercialApprovalResult:
        self.approval_calls += 1
        status = "APPROVED_MOCK" if approved else "REJECTED_MOCK"
        self.state.statuses[track_id] = status
        return CommercialApprovalResult(
            track_id=track_id,
            status=status,
            approved=approved,
            message=reason or "Synthetic mock commercial decision.",
            mock=True,
        )

    def acknowledge_receipt(self, track_id: str) -> ReceiptAcknowledgmentResult:
        self.receipt_acknowledgment_calls += 1
        return ReceiptAcknowledgmentResult(
            track_id=track_id,
            acknowledged=True,
            status="ACKNOWLEDGED_MOCK",
            message="Synthetic mock receipt acknowledgment; no DGII call occurred.",
            mock=True,
        )


class LiveDGIITransport:
    """Explicit placeholder that prevents all live DGII HTTP behavior."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "Live DGII transport is intentionally unavailable. Use MockDGIITransport "
            "for local contract tests; no production URLs or network calls are enabled."
        )
