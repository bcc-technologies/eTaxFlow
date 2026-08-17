"""Disabled public DGII endpoint stubs (503 JSON when not enabled)."""

from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def _disabled_payload() -> dict:
    return {
        "status": "DISABLED",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
    }


def _endpoint_response(request: HttpRequest) -> HttpResponse:
    if getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False):
        # Phase 025 does not implement live processing even when flag is true.
        return JsonResponse(
            {
                "status": "NOT_IMPLEMENTED",
                "compliance_status": "NOT_DGII_COMPLIANT",
                "dgii_submission_allowed": False,
                "detail": "Public DGII endpoint route exists but live processing is not implemented.",
            },
            status=503,
        )
    return JsonResponse(_disabled_payload(), status=503)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_recepcion_ecf(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/recepcion/api/ecf — no XML processing."""
    if request.body:
        # Do not parse or persist inbound XML in Phase 025.
        pass
    return _endpoint_response(request)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dgii_aprobacion_comercial_ecf(request: HttpRequest) -> HttpResponse:
    """Stub for /fe/aprobacioncomercial/api/ecf — no ACECF processing."""
    if request.body:
        pass
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
