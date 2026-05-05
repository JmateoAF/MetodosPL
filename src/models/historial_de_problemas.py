
class HistorialDeProblemas:

    def __init__(self):
        self.historial_de_problemas : list[dict] = []

    # Cuarda un problema y lo devuelve
    def ingresar_problema(self, datos_entrada : dict) -> dict:
        self.historial_de_problemas.append(datos_entrada)
        return datos_entrada

    # Devuelve el historial completo de problemas
    def obtener_historial_de_problemas(self) -> list[dict]:
        return self.historial_de_problemas

    # Devuelve un problema a partir de su indice
    def obtener_problemas(self, indice: int) -> dict:
        return self.historial_de_problemas[indice]

    # Elimina un problema a partir de su indice
    def eliminar_problema(self, indice : int) -> dict:
        return  self.historial_de_problemas.pop(indice)
