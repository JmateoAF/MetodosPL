# src/models/entity/programacion_lineal/problema.py

from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Union
from src.models.entity.programacion_lineal.enums import TipoOptimizacion, SignoRestriccion

# Tipo de dato estricto para soportar tanto precisión decimal como exacta
Numerico = Union[int, float, Fraction]


@dataclass(frozen=True)
class Restriccion:
    """
    Entidad inmutable que representa una restricción lineal en el dominio.
    Estructura matemática: a_i1*x_1 + a_i2*x_2 + ... [signo] rhs
    """
    coeficientes: List[Numerico]
    signo: SignoRestriccion
    rhs: Numerico

    def __post_init__(self) -> None:
        """Validación de integridad estructural de la restricción."""
        if not self.coeficientes:
            raise ValueError("La restricción debe contener al menos un coeficiente numérico.")


@dataclass(frozen=True)
class ProblemaPL:
    """
    Entidad del dominio que representa un Modelo de Programación Lineal completo.
    Garantiza inmutabilidad absoluta y consistencia dimensional en sus componentes.
    """
    tipo: TipoOptimizacion
    objetivo: List[Numerico]
    restricciones: List[Restriccion] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validación funcional estricta de las dimensiones del modelo matemático."""
        if not self.objetivo:
            raise ValueError("La función objetivo no puede estar vacía.")
        
        cantidad_variables_objetivo = len(self.objetivo)
        
        for indice, restriccion in enumerate(self.restricciones):
            if len(restriccion.coeficientes) != cantidad_variables_objetivo:
                raise ValueError(
                    f"""Inconsistencia en la restricción número {indice + 1}: 
Se esperaban {cantidad_variables_objetivo} coeficientes para emparejar 
con la función objetivo, pero se recibieron {len(restriccion.coeficientes)}."""
                )

    @property
    def total_variables(self) -> int:
        """Retorna la cantidad exacta de variables de decisión del modelo."""
        return len(self.objetivo)

    @property
    def total_restricciones(self) -> int:
        """Retorna la cantidad total de restricciones aplicadas al modelo."""
        return len(self.restricciones)