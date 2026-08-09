"""TrackId status consultation contract service."""

from .contracts import DGIIServiceTransport, StatusResult


def consult_status(transport: DGIIServiceTransport, track_id: str) -> StatusResult:
    return transport.consult_status(track_id)
