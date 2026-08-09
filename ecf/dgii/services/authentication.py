"""Authentication contract service."""

from .contracts import AuthenticationRequest, AuthenticationResult, DGIIServiceTransport


def authenticate(
    transport: DGIIServiceTransport,
    request: AuthenticationRequest,
) -> AuthenticationResult:
    return transport.authenticate(request)
