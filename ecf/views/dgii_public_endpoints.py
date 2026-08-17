"""Disabled public DGII endpoint stubs (503 JSON when not enabled)."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ecf.dgii.receiver import build_disabled_receiver_response


def disabled_endpoint_payload() -> dict:
    """Backward-compatible alias for disabled stub JSON."""
    return build_disabled_receiver_response()


def _endpoint_response(request: HttpRequest) -> HttpResponse:
    # Intentionally ignore request.body — no XML parse, no auth, no persistence.
    if getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False):
        return JsonResponse(
            {
                "status": "NOT_IMPLEMENTED",
                "compliance_status": "NOT_DGII_COMPLIANT",
                "dgii_submission_allowed": False,
                "track_id": None,
                "message": (
                    "Public DGII endpoint route exists but live processing is not implemented."
                ),
            },
            status=503,
        )
    return JsonResponse(build_disabled_receiver_response(), status=503)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_recepcion_ecf(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/recepcion/api/ecf — no XML processing."""
    return _endpoint_response(request)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_aprobacion_comercial_ecf(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/aprobacioncomercial/api/ecf — no ACECF processing."""
    return _endpoint_response(request)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_autenticacion_semilla(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/autenticacion/api/semilla — no seed/token issuance."""
    return _endpoint_response(request)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_autenticacion_validacioncertificado(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/autenticacion/api/validacioncertificado — no cert validation."""
    return _endpoint_response(request)
