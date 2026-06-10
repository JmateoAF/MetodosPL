# src/utils/conversor_entrada.py

from fractions import Fraction
from src.models.entity.programacion_lineal.respuesta import NumericoTabular

class ConversorEntrada:
    """Transforma entradas textuales crudas de la UI a objetos numéricos puros con tipado estático."""

    @classmethod
    def texto_a_numerico_exacto(cls, texto: str) -> NumericoTabular:
        """
        Parsea cadenas de texto complejas provenientes de los campos de texto de Flet.
        Soporta enteros ('5'), decimales ('2.5') y fracciones textuales ('3/4').
        """
        texto_limpio = texto.strip().replace(" ", "")
        if not texto_limpio:
            return Fraction(0, 1)

        try:
            if "/" in texto_limpio:
                numerador_str, denominador_str = texto_limpio.split("/", 1)
                return Fraction(int(numerador_str), int(denominador_str))
            
            # Soporte nativo para decimales convirtiéndolos primero a float y luego a Fraction exacta
            if "." in texto_limpio:
                return Fraction(float(texto_limpio)).limit_denominator()
                
            return Fraction(int(texto_limpio), 1)
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError(f"El formato numérico '{texto}' no es válido para el modelo matemático. Detalles: {error}")