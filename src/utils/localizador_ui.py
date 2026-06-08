# src/utils/localizador_ui.py

from src.models.entity.respuesta import IteracionTabular

class LocalizadorUI:
    """Provee mapas de coordenadas visuales para asistir a las vistas en el resaltado de pivotes."""

    @classmethod
    def es_celda_pivote(cls, iteracion: IteracionTabular, indice_fila: int, indice_columna: int) -> bool:
        """
        Determina si una coordenada específica dentro del DataTable de Flet corresponde al cruce del pivote.
        Compensa automáticamente el hecho de que la matriz del snapshot incluye la columna 'Base' antepuesta.
        """
        if iteracion.fila_pivote is None or iteracion.col_pivote is None:
            return False

        # Compensación de índices: 
        # La primera columna visual es 'Base'. Por ende, las columnas numéricas reales de datos se desplazan +1.
        columna_ajustada_ui = iteracion.col_pivote + 1
        fila_ajustada_ui = iteracion.fila_pivote

        return indice_fila == fila_ajustada_ui and indice_columna == columna_ajustada_ui
    