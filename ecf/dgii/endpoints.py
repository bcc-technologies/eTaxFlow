"""DGII public endpoint metadata and URL composition (design-only).

Does not call DGII, perform network checks, or claim compliance.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings


def _normalize_base_url(base: str) -> str:
    return (base or "").strip().rstrip("/")


def _compose_url(base: str, path: str) -> str:
    base_norm = _normalize_base_url(base)
    if not base_norm:
        return ""
    path_norm = path if path.startswith("/") else f"/{path}"
    return f"{base_norm}{path_norm}"


def _endpoint_readiness_status(*, base_url: str, endpoints_enabled: bool) -> str:
    if not base_url:
        return "BLOCKED"
    if not endpoints_enabled:
        return "DESIGN_ONLY"
    # Enabled flag alone is insufficient for READY; later phases add verification.
    return "DESIGN_ONLY"


def get_software_registration_metadata() -> dict[str, Any]:
    """Return planned DGII software registration fields and composed URLs."""
    software_type = getattr(settings, "ETAXFLOW_SOFTWARE_TYPE", "PROPIO")
    software_name = getattr(settings, "ETAXFLOW_SOFTWARE_NAME", "eTaxFlow")
    software_version = getattr(settings, "ETAXFLOW_SOFTWARE_VERSION", "0.1.0")
    public_base_url = _normalize_base_url(getattr(settings, "ETAXFLOW_PUBLIC_BASE_URL", ""))
    recepcion_path = getattr(
        settings, "ETAXFLOW_DGII_RECEPCION_PATH", "/fe/recepcion/api/ecf"
    )
    aprobacion_path = getattr(
        settings,
        "ETAXFLOW_DGII_APROBACION_COMERCIAL_PATH",
        "/fe/aprobacioncomercial/api/ecf",
    )
    autenticacion_template = getattr(
        settings,
        "ETAXFLOW_DGII_AUTENTICACION_PATH_TEMPLATE",
        "/fe/autenticacion/api/[semilla]validacioncertificado",
    )
    endpoints_enabled = bool(getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False))

    recepcion_url = _compose_url(public_base_url, recepcion_path)
    aprobacion_comercial_url = _compose_url(public_base_url, aprobacion_path)
    autenticacion_url_template = (
        _compose_url(public_base_url, autenticacion_template) if public_base_url else ""
    )

    readiness_status = _endpoint_readiness_status(
        base_url=public_base_url,
        endpoints_enabled=endpoints_enabled,
    )

    url_status = "BLOCKED" if not public_base_url else readiness_status

    endpoints_enabled_flag = endpoints_enabled
    deployment_readiness_status = "BLOCKED"
    endpoint_routes_status = "DISABLED" if not endpoints_enabled_flag else "NOT_IMPLEMENTED"

    return {
        "software_type": software_type,
        "software_name": software_name,
        "software_version": software_version,
        "public_base_url": public_base_url,
        "public_base_url_configured": bool(public_base_url),
        "recepcion_path": recepcion_path,
        "aprobacion_comercial_path": aprobacion_path,
        "autenticacion_path_template": autenticacion_template,
        "recepcion_url": recepcion_url,
        "aprobacion_comercial_url": aprobacion_comercial_url,
        "autenticacion_url_template": autenticacion_url_template,
        "endpoints_enabled": endpoints_enabled_flag,
        "readiness_status": readiness_status,
        "url_status": url_status,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "design_only": True,
        "planned_host": "etaxflow.bcctechnologies.com.do",
        "planned_host_example": "etaxflow.bcctechnologies.com.do",
        "staging_dns_status": "UNVERIFIED",
        "staging_ssl_status": "UNVERIFIED",
        "staging_external_reachability_status": "UNVERIFIED",
        "endpoint_routes_status": endpoint_routes_status,
        "deployment_readiness_status": deployment_readiness_status,
        "manual_verification_required": True,
    }
