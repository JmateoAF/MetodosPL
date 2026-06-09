# src/models/entity/respuesta.py

from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Union
import numpy as np
from src.models.entity.enums import EstadoProblema

# Tipo de dato estricto para valores numéricos algebraicos
NumericoTabular = Union[int, float, Fraction]


@dataclass(frozen=True)
class IteracionTabular:
    """
    Representa el estado absoluto, aislado e independiente de un Tableau Simplex.
    Cada paso del algoritmo se auto-describe por completo.
    """
    tabla: np.ndarray              # Matriz NumPy (dtype=object) con los coeficientes (Fraction)
    encabezados: List[str]         # Nombres de las columnas en esta iteración específica
    variables_base: List[str]      # Nombres de las variables básicas asignadas a las filas
    mensaje: str                  # Descripción del cambio de base (ej. qué variable entra/sale)
    fila_pivote: Optional[int] = None
    col_pivote: Optional[int] = None
    fase: Optional[int] = None     # Indicador opcional de fase (1 o 2) para el método de las Dos Fases

    def __post_init__(self) -> None:
        """Validación de consistencia matricial interna de la iteración."""
        if not isinstance(self.tabla, np.ndarray):
            raise TypeError("La estructura de la tabla debe ser un objeto numpy.ndarray.")
        
        num_columnas = self.tabla.shape[1]
        if len(self.encabezados) != num_columnas:
            raise ValueError(
                f"Inconsistencia en columnas: La tabla tiene {num_columnas} columnas, "
                f"pero se proporcionaron {len(self.encabezados)} encabezados."
            )
        
        num_filas_restricciones = self.tabla.shape[0] - 1
        if len(self.variables_base) != num_filas_restricciones:
            raise ValueError(
                f"Inconsistencia en filas básicas: La tabla tiene {num_filas_restricciones} "
                f"filas de restricciones, pero se asignaron {len(self.variables_base)} variables a la base."
            )


@dataclass(frozen=True)
class RespuestaTabularPL:
    """
    Entidad del dominio para las respuestas de los solucionadores matriciales paso a paso
    (Simplex Tabular, Gran M y Dos Fases).
    """
    estado: EstadoProblema
    mensaje: str
    z_optimo: Optional[NumericoTabular] = None
    variables_decision: Optional[List[NumericoTabular]] = None
    iteraciones: List[IteracionTabular] = field(default_factory=list)


@dataclass(frozen=True)
class RespuestaSciPyPL:
    """
    Entidad del dominio que encapsula al 100% y de forma nativa todos los datos 
    devueltos por el objeto OptimizeResult de scipy.optimize.linprog.
    """
    estado: EstadoProblema       # Estado unificado del sistema
    mensaje: str                 # Mensaje unificado del sistema
    
    # --- Datos crudos e íntegros de scipy.optimize.linprog ---
    x: Optional[List[float]]     # Vector solución óptima (Variables de decisión)
    fun: Optional[float]         # Valor óptimo de la función objetivo
    status: int                  # Código de estado nativo de SciPy (0 a 4)
    message: str                 # Mensaje nativo explicativo de SciPy
    nit: int                     # Número total de iteraciones ejecutadas
    slack: Optional[List[float]] # Valores de variables de holgura/exceso finales
    con: Optional[List[float]]   # Residuos de las restricciones de igualdad
    success: bool                # Indicador booleano nativo de éxito de la optimización