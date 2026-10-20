from django.urls import path

from ecf.views.dgii_public_endpoints import (
    dgii_aprobacion_comercial_ecf,
    dgii_autenticacion_semilla,
    dgii_autenticacion_validacioncertificado,
    dgii_recepcion_ecf,
)

urlpatterns = [
    path("fe/recepcion/api/ecf", dgii_recepcion_ecf, name="dgii_recepcion_ecf"),
    path(
        "fe/aprobacioncomercial/api/ecf",
        dgii_aprobacion_comercial_ecf,
        name="dgii_aprobacion_comercial_ecf",
    ),
    path(
        "fe/autenticacion/api/semilla",
        dgii_autenticacion_semilla,
        name="dgii_autenticacion_semilla",
    ),
    path(
        "fe/autenticacion/api/validacioncertificado",
        dgii_autenticacion_validacioncertificado,
        name="dgii_autenticacion_validacioncertificado",
    ),
]
