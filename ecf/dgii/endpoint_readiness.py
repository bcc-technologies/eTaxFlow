"""Build endpoint readiness checks for dgii_readiness_report."""

from __future__ import annotations

from typing import Any

from ecf.dgii.endpoints import get_software_registration_metadata


def build_endpoint_readiness_checks() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Return (endpoint_checks dict, additional blocker checks list)."""
    meta = get_software_registration_metadata()
    base_url = meta["public_base_url"]
    endpoints_enabled = meta["endpoints_enabled"]

    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    additional = [
        _check(
            "public_base_url_not_configured",
            "BLOCKED" if not base_url else "DESIGN_ONLY",
            (
                "ETAXFLOW_PUBLIC_BASE_URL is blank; portal URLs cannot be composed."
                if not base_url
                else f"Base URL configured ({base_url}) but not deployment-verified."
            ),
            blocker=not base_url,
        ),
        _check(
            "public_dgii_endpoints_disabled",
            "DESIGN_ONLY" if not endpoints_enabled else "PARTIAL",
            (
                "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS is false; route stubs return 503 DISABLED."
                if not endpoints_enabled
                else "Endpoints flag enabled but live processing remains NOT_IMPLEMENTED."
            ),
            blocker=True,
        ),
        _check(
            "endpoint_ssl_not_verified",
            "BLOCKED",
            "HTTPS/TLS for public DGII-facing host is not verified.",
        ),
        _check(
            "endpoint_internet_access_not_verified",
            "BLOCKED",
            "Internet accessibility of receiver/auth URLs is not verified.",
        ),
        _check(
            "endpoint_routes_not_implemented_or_not_verified",
            "NOT_IMPLEMENTED",
            "Receiver/auth routes are design stubs only; no real XML/auth processing.",
        ),
        # Phase 026 — staging DNS/SSL deployment checklist blockers (manual verification only)
        _check(
            "staging_dns_not_verified",
            "UNVERIFIED",
            "Staging/pre-cert DNS for planned host is not verified (manual dig check pending).",
        ),
        _check(
            "staging_ssl_not_verified",
            "UNVERIFIED",
            "HTTPS/TLS certificate for staging/pre-cert host is not verified.",
        ),
        _check(
            "staging_external_reachability_not_verified",
            "UNVERIFIED",
            "External internet reachability of staging/pre-cert host is not verified.",
        ),
        _check(
            "staging_environment_not_deployed",
            "BLOCKED",
            "Staging/pre-cert environment is not deployed; checklist only in repo.",
        ),
        _check(
            "public_endpoint_routes_disabled",
            meta["endpoint_routes_status"],
            "Public /fe/... route stubs remain disabled (503 DISABLED JSON).",
        ),
        _check(
            "disabled_stub_only",
            "DISABLED",
            "Only disabled stub responses are available; no live receiver/auth processing.",
        ),
        _check(
            "production_signing_not_approved",
            "BLOCKED",
            "Production signing architecture is not approved; signing settings remain disabled.",
        ),
        _check(
            "endpoint_security_owner_not_assigned",
            "MANUAL_REQUIRED",
            "Endpoint/security owner for staging exposure is not recorded in governance gate.",
        ),
    ]

    recepcion_status = meta["url_status"] if base_url else "BLOCKED"
    aprobacion_status = meta["url_status"] if base_url else "BLOCKED"
    autenticacion_status = meta["url_status"] if base_url else "BLOCKED"

    endpoint_checks = {
        "url_recepcion": {
            "name": "url_recepcion",
            "status": recepcion_status,
            "detail": (
                "No public base URL; recepcion URL blocked."
                if not meta["recepcion_url"]
                else f"Planned recepcion URL: {meta['recepcion_url']} (design only)."
            ),
            "blocker": True,
            "planned_url": meta["recepcion_url"],
        },
        "recepcion_url_blocked": {
            "name": "recepcion_url_blocked",
            "status": "BLOCKED",
            "detail": "Recepcion URL not deployment-ready for DGII portal submission.",
            "blocker": True,
        },
        "url_aprobacion_comercial": {
            "name": "url_aprobacion_comercial",
            "status": aprobacion_status,
            "detail": (
                "No public base URL; aprobacion URL blocked."
                if not meta["aprobacion_comercial_url"]
                else f"Planned aprobacion URL: {meta['aprobacion_comercial_url']} (design only)."
            ),
            "blocker": True,
            "planned_url": meta["aprobacion_comercial_url"],
        },
        "aprobacion_comercial_url_blocked": {
            "name": "aprobacion_comercial_url_blocked",
            "status": "BLOCKED",
            "detail": "Aprobacion Comercial URL not deployment-ready for DGII portal submission.",
            "blocker": True,
        },
        "url_autenticacion": {
            "name": "url_autenticacion",
            "status": autenticacion_status,
            "detail": (
                "No public base URL; autenticacion URL blocked."
                if not meta["autenticacion_url_template"]
                else f"Planned autenticacion template: {meta['autenticacion_url_template']} (design only)."
            ),
            "blocker": True,
            "planned_url": meta["autenticacion_url_template"],
        },
        "autenticacion_url_blocked": {
            "name": "autenticacion_url_blocked",
            "status": "BLOCKED",
            "detail": "Autenticacion URL not deployment-ready for DGII portal submission.",
            "blocker": True,
        },
    }

    return endpoint_checks, additional
