import sys
import logging
from modules.invoice import Invoice
from modules.client import Client

# Configuración de logging
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    print("=== Sistema de Facturación Electrónica (eTaxFlow) ===")

    # Ejemplo: crear un cliente
    cliente = Client(
        nombre="Juan Pérez",
        rnc="123456789",
        direccion="Av. Independencia #123, Santo Domingo"
    )

    # Ejemplo: crear una factura
    factura = Invoice(
        numero="F001-00000001",
        cliente=cliente,
        items=[
            {"descripcion": "Laptop Lenovo", "cantidad": 1, "precio": 45000},
            {"descripcion": "Mouse inalámbrico", "cantidad": 2, "precio": 800}
        ],
        impuestos={"ITBIS": 0.18}
    )

    # Calcular totales
    factura.calcular_totales()

    # Mostrar resumen
    print(factura.resumen())

    # Guardar en JSON y XML (para DGII)
    factura.exportar("json", "factura_0001.json")
    factura.exportar("xml", "factura_0001.xml")

    logging.info("Factura generada exitosamente")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Error en la ejecución: {e}")
        sys.exit(1)
