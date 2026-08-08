import json
import xml.etree.ElementTree as ET
from datetime import datetime


class Invoice:
    def __init__(self, numero, cliente, items, impuestos, tipo="Factura de Consumo"):
        self.numero = numero  # NCF
        self.cliente = cliente  # instancia de Client
        self.items = (
            items  # lista de diccionarios con 'descripcion', 'cantidad', 'precio'
        )
        self.impuestos = impuestos  # diccionario con tipos de impuestos y sus tasas
        self.tipo = tipo  # Tipo de comprobante
        self.total = 0  # total a calcular
        self.fecha_emision = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )  # Fecha y hora de emisión

    def calcular_totales(self):
        subtotal = sum(item["cantidad"] * item["precio"] for item in self.items)
        itbis = subtotal * self.impuestos.get("ITBIS", 0)
        self.total = subtotal + itbis
        return self.total

    def resumen(self):
        return {
            "NCF": self.numero,
            "Tipo": self.tipo,
            "Cliente": self.cliente.nombre,
            "RNC": self.cliente.rnc,
            "Total": self.total,
        }

    def exportar(self, formato, filename):
        if formato == "json":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.resumen(), f, ensure_ascii=False, indent=4)
        elif formato == "xml":
            self.exportar_ecf(filename)

    def exportar_ecf(self, filename):
        # Nodo raíz
        factura = ET.Element("eCF")

        # Encabezado
        encabezado = ET.SubElement(factura, "Encabezado")
        ET.SubElement(encabezado, "NCF").text = self.numero
        ET.SubElement(encabezado, "TipoComprobante").text = self.tipo
        ET.SubElement(encabezado, "FechaEmision").text = self.fecha_emision

        emisor = ET.SubElement(encabezado, "Emisor")
        ET.SubElement(emisor, "RNC").text = "133085771"  # tu RNC
        ET.SubElement(emisor, "RazonSocial").text = "BCC Technologies SRL"
        ET.SubElement(emisor, "Direccion").text = (
            "Calle juan tomás díaz #103, Santo Domingo"
        )
        ET.SubElement(emisor, "Telefono").text = "809-519-3767"
        ET.SubElement(emisor, "Email").text = "bcctechrd@gmail.com"

        receptor = ET.SubElement(encabezado, "Receptor")
        ET.SubElement(receptor, "RNC").text = self.cliente.rnc
        ET.SubElement(receptor, "Nombre").text = self.cliente.nombre
        ET.SubElement(receptor, "Direccion").text = (
            self.cliente.direccion if hasattr(self.cliente, "direccion") else "N/A"
        )
        ET.SubElement(receptor, "Telefono").text = (
            self.cliente.telefono if hasattr(self.cliente, "telefono") else "N/A"
        )
        ET.SubElement(receptor, "Email").text = (
            self.cliente.email if hasattr(self.cliente, "email") else "N/A"
        )

        # Detalles
        detalles = ET.SubElement(factura, "Detalles")
        for item in self.items:
            item_el = ET.SubElement(detalles, "Item")
            ET.SubElement(item_el, "Codigo").text = item.get("codigo", "N/A")
            ET.SubElement(item_el, "Descripcion").text = item["descripcion"]
            ET.SubElement(item_el, "Cantidad").text = str(item["cantidad"])
            ET.SubElement(item_el, "PrecioUnitario").text = str(item["precio"])
            subtotal_item = item["cantidad"] * item["precio"]
            ET.SubElement(item_el, "Subtotal").text = str(subtotal_item)

        # Totales
        totales = ET.SubElement(factura, "Totales")
        subtotal = sum(item["cantidad"] * item["precio"] for item in self.items)
        ET.SubElement(totales, "Subtotal").text = str(subtotal)
        ET.SubElement(totales, "ITBIS").text = str(
            subtotal * self.impuestos.get("ITBIS", 0)
        )
        ET.SubElement(totales, "Total").text = str(self.total)

        # Firma digital y QR (placeholder)
        ET.SubElement(factura, "FirmaDigital").text = "PENDIENTE"
        ET.SubElement(factura, "CodigoQR").text = "PENDIENTE"

        # Guardar archivo
        tree = ET.ElementTree(factura)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
