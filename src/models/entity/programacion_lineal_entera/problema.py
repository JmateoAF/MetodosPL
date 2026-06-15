# src/models/entity/programacion_lineal_entera/problema.py

from dataclasses import dataclass, field
from typing import List, Optional, Union
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal_entera.enums import (
    TipoVariable,
    OperadorLogico,
    OperadorMGrande,
    OperadorAsignacionLogica
)
from src.models.entity.programacion_lineal.problema import Restriccion


@dataclass(frozen=True)
class NodoLogico:
    """
    Representa un nodo en el árbol de expresiones lógicas (AST).
    Permite anidar y evaluar estructuras lógicas puras, avanzadas (M Grande) 
    y de asignación reificada de forma infinita.
    """
    # El operador que une a los hijos (Puro, M Grande o de Asignación/Evaluación)
    operador: Union[OperadorLogico, OperadorMGrande, OperadorAsignacionLogica]
    
    # Hijos del nodo: pueden ser restricciones matemáticas: Restriccion, sub-nodos (paréntesis): NodoLogico
    # o variables binarias individuales (para las asignaciones lógicas evaluativas): str
    hijos: List[Union[Restriccion, "NodoLogico", str]] = field(default_factory=list)
    
    # Almacena el identificador o nombre de la variable binaria (directa x1, x2,... o artificial 'a_i') 
    # que captura/reifica el resultado de la evaluación de este bloque intermedio.
    variable_control_asociada: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.hijos:
            raise ValueError("Un nodo lógico no puede estar vacío, debe contener elementos hijos.")


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