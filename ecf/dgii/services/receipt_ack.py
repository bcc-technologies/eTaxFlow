"""Receipt acknowledgment contract service."""

from .contracts import DGIIServiceTransport, ReceiptAcknowledgmentResult


def acknowledge_receipt(
    transport: DGIIServiceTransport,
    track_id: str,
) -> ReceiptAcknowledgmentResult:
    return transport.acknowledge_receipt(track_id)
