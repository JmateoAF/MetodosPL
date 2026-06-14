# src/models/entity/programacion_lineal_entera/problema.py

from dataclasses import dataclass, field
from typing import List, Optional, Union
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal_entera.enums import TipoVariable, OperadorLogico, OperadorMGrande
from src.models.entity.programacion_lineal.problema import Restriccion


@dataclass(frozen=True)
class NodoLogico:
    """
    Representa un nodo en el árbol de expresiones lógicas (AST).
    Permite anidar paréntesis de forma infinita sin alterar el backend.
    """
    # El operador que une a los hijos (puede ser de Álgebra Pura o M Grande)
    operador: Union[OperadorLogico, OperadorMGrande]
    
    # Hijos del nodo: pueden ser restricciones matemáticas puras o sub-nodos (paréntesis)
    hijos: List[Union[Restriccion, NodoLogico]] = field(default_factory=list)
    
    # Variable binaria opcional que almacena el resultado/activación de este bloque intermedio
    variable_control_asociada: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.hijos:
            raise ValueError("Un nodo lógico no puede estar vacío, debe contener hijos.")


@dataclass(frozen=True)
class ProblemaPLE(ProblemaPL):
    """
    Entidad del dominio para Modelos de Programación Lineal Entera (Pura, Mixta o Binaria).
    Hereda la estructura algebraica y añade el vector de categorías de variables.
    """
    tipos_variables: List[TipoVariable] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Ejecuta primero las validaciones de dimensiones de la clase padre (ProblemaPL)
        super().__post_init__()
        
        if not self.tipos_variables:
            raise ValueError("Se debe especificar el tipo de cada variable de decisión.")
            
        if len(self.tipos_variables) != self.total_variables:
            raise ValueError(
                f"Inconsistencia en tipos de variables: El modelo tiene {self.total_variables} "
                f"variables, pero se definieron {len(self.tipos_variables)} tipos."
            )


@dataclass(frozen=True)
class ProblemaModeladoLogico(ProblemaPLE):
    """
    Entidad del dominio definitiva que captura el modelo de datos extendido.
    Soporta restricciones algebraicas, relaciones booleanas puras y condicionales M Grande.
    """
    arboles_logicos: List[NodoLogico] = field(default_factory=list)