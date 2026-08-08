class Client:
    def __init__(self, nombre, rnc, direccion, telefono, email=None):
        self.nombre = nombre
        self.rnc = rnc
        self.direccion = direccion
        self.telefono = telefono
        self.email = email  # opcional
