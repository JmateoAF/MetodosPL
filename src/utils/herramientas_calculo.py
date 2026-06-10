# src/utils/herramientas_calculo.py
"""
herramientas_calculo.py
=======================
Módulo de utilidades matemáticas para el procesamiento y formateo pedagógico
de los coeficientes algebraicos exactos en el motor de optimización.

Responsabilidades:
    - Extraer y aislar de forma exacta la penalización virtual M en el método de la M Grande.
    - Simplificar y formatear objetos Fraction y flotantes a cadenas de texto limpias para la UI.

Autor: Utilities Calculation Module — MVC Linear Optimizer
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple
from src.models.entity.respuesta import NumericoTabular


@dataclass(frozen=True)
class CoeficienteMGrande:
    """
    Entidad inmutable que representa un valor en el dominio de la M Grande.
    Estructura matemática: constante_real + cantidad_m * M
    """
    constante_real: Fraction
    cantidad_m: Fraction

    def __str__(self) -> str:
        """Devuelve la representación en lenguaje natural matemático para la interfaz."""
        if self.cantidad_m == 0:
            return f"{self.constante_real}"
        
        # Formatear el término M
        if self.cantidad_m == 1:
            termino_m = "+ M"
        elif self.cantidad_m == -1:
            termino_m = "- M"
        else:
            termino_m = f"{self.cantidad_m}M" if self.cantidad_m < 0 else f"+ {self.cantidad_m}M"

        if self.constante_real == 0:
            # Eliminar el "+" inicial si la constante es cero
            return termino_m.lstrip("+ ").strip()
            
        return f"{self.constante_real} {termino_m}".strip()


class AnalizadorMatematico:
    """
    Procesador funcional estático para la conversión y análisis de estructuras
    numéricas complejas dentro de las iteraciones matriciales.
    """

    VALOR_M_REFERENCIA: Fraction = Fraction(10 ** 9, 1)

    @classmethod
    def extraer_componente_m(cls, valor: Fraction) -> CoeficienteMGrande:
        """
        Analiza un coeficiente fraccionario del Tableau y extrae algebraicamente 
        la cantidad de veces que contiene la penalización M (10^9).

        Ejemplo:
            Fraction(2000000005, 1) -> CoeficienteMGrande(constante_real=5, cantidad_m=2) -> "5 + 2M"
        """
        # Operaciones algebraicas exactas usando aritmética funcional fraccionaria
        numerador = valor.numerator
        denominador = valor.denominator

        # Obtener el valor de M bajo el denominador actual
        m_actual = cls.VALOR_M_REFERENCIA

        # Calcular cuántas M enteras y fraccionarias están presentes
        cantidad_m = Fraction(int(round(float(valor / m_actual))), 1)
        constante_real = valor - (cantidad_m * m_actual)

        return CoeficienteMGrande(constante_real=constante_real, cantidad_m=cantidad_m)

    @classmethod
    def formatear_valor_pedagogico(cls, valor: NumericoTabular, evaluar_m: bool = False) -> str:
        """
        Toma un valor numérico del motor matemático y lo simplifica a su forma
        más limpia y elegante para ser renderizado en las celdas de la UI.
        
        - Si es una fracción con denominador 1, muestra el entero.
        - Si es un flotante redondo, elimina los decimales innecesarios.
        - Si evaluar_m es True, traduce las cantidades gigantescas a notación "M".
        """
        if isinstance(valor, Fraction):
            # Forzar la simplificación interna nativa de la biblioteca fractions
            fraccion_simplificada = valor.limit_denominator()
            
            if evaluar_m and abs(fraccion_simplificada) >= cls.VALOR_M_REFERENCIA / 10:
                return str(cls.extraer_componente_m(fraccion_simplificada))

            if fraccion_simplificada.denominator == 1:
                return str(fraccion_simplificada.numerator)
            return f"{fraccion_simplificada.numerator}/{fraccion_simplificada.denominator}"

        if isinstance(valor, (int, float)):
            valor_float = float(valor)
            if valor_float.is_integer():
                return str(int(valor_float))
            return f"{valor_float:.4f}".rstrip('0').rstrip('.')

        return str(valor)
