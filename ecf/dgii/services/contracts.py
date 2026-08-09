"""Transport-neutral DGII service contract dataclasses.

These contracts model the shape of future integrations only. They do not
authorize calls or imply that eTaxFlow is DGII-compliant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class DGIIServiceConfiguration:
    environment: str = "MOCK"
    software_name: str = "eTaxFlow"
    software_version: str = "MVP"
    software_type: str = "INTERNAL"
    url_recepcion: str = ""
    url_aprobacion_comercial: str = ""
    url_autenticacion: str = ""
    live_transport_enabled: bool = False


@dataclass(frozen=True)
class AuthenticationRequest:
    software_name: str
    software_version: str
    software_type: str
    credential_reference: str | None = None


@dataclass(frozen=True)
class AuthenticationResult:
    access_token: str
    expires_at: datetime | None = None
    mock: bool = True
    message: str = ""


@dataclass(frozen=True)
class ReceptionRequest:
    xml_bytes: bytes
    invoice_internal_code: str
    ecf_type: str = "31"


@dataclass(frozen=True)
class ReceptionResult:
    track_id: str
    status: str
    message: str = ""
    mock: bool = True


@dataclass(frozen=True)
class StatusResult:
    track_id: str
    status: str
    status_message: str = ""
    mock: bool = True


@dataclass(frozen=True)
class CommercialApprovalResult:
    track_id: str
    status: str
    approved: bool
    message: str = ""
    mock: bool = True


@dataclass(frozen=True)
class ReceiptAcknowledgmentResult:
    track_id: str
    acknowledged: bool
    status: str
    message: str = ""
    mock: bool = True


class DGIIServiceTransport(Protocol):
    """Protocol implemented by a future approved transport or the mock."""

    def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        ...

    def submit_reception(self, request: ReceptionRequest) -> ReceptionResult:
        ...

    def consult_status(self, track_id: str) -> StatusResult:
        ...

    def commercial_approval(
        self, track_id: str, *, approved: bool, reason: str = ""
    ) -> CommercialApprovalResult:
        ...

    def acknowledge_receipt(self, track_id: str) -> ReceiptAcknowledgmentResult:
        ...


@dataclass
class MockTransportState:
    statuses: dict[str, str] = field(default_factory=dict)
    status_messages: dict[str, str] = field(default_factory=dict)
    next_track_number: int = 1
