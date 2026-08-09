"""Practical local inventory status for DGII official sources."""

from __future__ import annotations

from pathlib import Path

SOURCES_DIR = Path("docs/dgii/sources")

EXPECTED_SOURCES = {
    "Informe_Tecnico_e-CF_v1.0.pdf": "Informe Técnico e-CF v1.0",
    "Descripcion_Tecnica_Servicios_DGII.pdf": "Descripción Técnica Servicios DGII",
    "Descripcion_Tecnica_Servicios_Emisores_Electronicos.pdf": "Descripción Técnica Servicios Emisores Electrónicos",
    "Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf": "Formato Comprobante Fiscal Electrónico e-CF v1.0",
    "Formato_Acuse_de_Recibo_v1.0.pdf": "Formato Acuse de Recibo v1.0",
    "Formato_Aprobacion_Comercial_v1.0.pdf": "Formato Aprobación Comercial v1.0",
    "Representacion_Impresa_e-CF.pdf": "Representación Impresa e-CF",
    "e-CF_31_v1.0.xsd": "XSD e-CF 31 v1.0",
    "Norma_General_01-2020.pdf": "Norma General 01-2020",
    "Ley_32-23.pdf": "Ley 32-23",
    "Decreto_587-24.pdf": "Decreto 587-24",
}


def source_inventory_status() -> dict:
    present = []
    missing = []
    for filename, label in EXPECTED_SOURCES.items():
        path = SOURCES_DIR / filename
        entry = {"filename": filename, "label": label, "path": str(path)}
        if path.exists() and path.stat().st_size > 0:
            present.append(entry)
        else:
            missing.append(entry)
    total = len(EXPECTED_SOURCES)
    return {
        "sources_dir": str(SOURCES_DIR),
        "expected_count": total,
        "collected_count": len(present),
        "missing_count": len(missing),
        "collected": present,
        "missing": missing,
        "summary": f"{len(present)}/{total} priority official sources present locally",
    }
