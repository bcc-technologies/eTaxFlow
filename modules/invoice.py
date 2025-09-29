import json
import xml.etree.ElementTree as ET

class Invoice:
    def __init__(self, numero, cliente, items, impuestos):
        self.numero = numero
        self.cliente = cliente
        self.items = items
        self.impuestos = impuestos
        self.total = 0

    def calcular_totales(self):
        subtotal = sum(item["cantidad"] * item["precio"] for item in self.items)
        itbis = subtotal * self.impuestos.get("ITBIS", 0)
        self.total = subtotal + itbis
        return self.total

    def resumen(self):
        return {
            "Factura": self.numero,
            "Cliente": self.cliente.nombre,
            "RNC": self.cliente.rnc,
            "Total": self.total
        }

    def exportar(self, formato, filename):
        if formato == "json":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.resumen(), f, ensure_ascii=False, indent=4)
        elif formato == "xml":
            self.exportar_xml(filename)

    def exportar_xml(self, filename):
        factura = ET.Element("FacturaElectronica")
        ET.SubElement(factura, "Numero").text = self.numero
        ET.SubElement(factura, "Cliente").text = self.cliente.nombre
        ET.SubElement(factura, "RNC").text = self.cliente.rnc
        ET.SubElement(factura, "Direccion").text = self.cliente.direccion

        items_el = ET.SubElement(factura, "Items")
        for item in self.items:
            item_el = ET.SubElement(items_el, "Item")
            ET.SubElement(item_el, "Descripcion").text = item["descripcion"]
            ET.SubElement(item_el, "Cantidad").text = str(item["cantidad"])
            ET.SubElement(item_el, "Precio").text = str(item["precio"])

        impuestos_el = ET.SubElement(factura, "Impuestos")
        for k, v in self.impuestos.items():
            ET.SubElement(impuestos_el, k).text = str(v)

        ET.SubElement(factura, "Total").text = str(self.total)

        tree = ET.ElementTree(factura)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

