"""e-CF reception contract service."""

from .contracts import DGIIServiceTransport, ReceptionRequest, ReceptionResult


def submit_reception(
    transport: DGIIServiceTransport,
    request: ReceptionRequest,
) -> ReceptionResult:
    return transport.submit_reception(request)
