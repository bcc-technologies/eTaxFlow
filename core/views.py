"""Core HTTP views."""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request: HttpRequest) -> HttpResponse:
    """
    Liveness probe for Render.

    Returns HTTP 200 with no authentication, no DGII activity, and no
    database reads or writes.
    """
    return HttpResponse("ok", content_type="text/plain", status=200)
