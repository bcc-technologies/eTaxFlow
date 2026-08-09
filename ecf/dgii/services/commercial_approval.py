"""Commercial approval/rejection contract service."""

from .contracts import CommercialApprovalResult, DGIIServiceTransport


def request_commercial_approval(
    transport: DGIIServiceTransport,
    track_id: str,
    *,
    approved: bool,
    reason: str = "",
) -> CommercialApprovalResult:
    return transport.commercial_approval(track_id, approved=approved, reason=reason)
