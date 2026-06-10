# src/models/entity/programacion_lineal/enums.py

from enum import Enum, unique

@unique
class TipoOptimizacion(Enum):
    """Define el objetivo principal de la optimización."""
    MAX = "MAX"
    MIN = "MIN"


@unique
class SignoRestriccion(Enum):
    """Operadores relacionales permitidos para los límites de las restricciones."""
    MENOR_IGUAL = "<="
    MAYOR_IGUAL = ">="
    IGUAL = "=="


@unique
class EstadoProblema(Enum):
    """
    Única fuente de verdad para todos los estados posibles en optimización.
    Mapea de forma semántica los resultados de cualquier solucionador del sistema.
    """
    # === 1. ESTADOS DE ÉXITO ===
    OPTIMO = "El solucionador encontró la respuesta óptima global y válida."
    OPTIMO_LOCAL = "Se encontró una solución óptima en la zona cercana, pero podrían existir mejores opciones."
    CONVERGENCIA_TOLERANCIA = "El proceso se detuvo porque las mejoras consecutivas son insignificantes."

    # === 2. ANOMALÍAS MATEMÁTICAS ===
    INVIABLE = "El problema no tiene solución porque las condiciones se contradicen entre sí."
    NO_ACOTADO = "El beneficio o costo puede crecer o decrecer indefinidamente sin ningún límite."
    DEGENERADO = "Existe un empate numérico en el proceso que podría ciclar el cálculo de forma infinita."
    PUNTO_ENSILLADURA = "El cálculo se estancó en una zona plana que no representa ni un máximo ni un mínimo."

    # === 3. LIMITACIONES COMPUTACIONALES ===
    LIMITE_ITERACIONES = "Se agotó el número máximo de intentos permitidos sin lograr resolver el problema."
    DIFICULTADES_NUMERICAS = "Ocurrió un error de precisión en los cálculos debido a números extremadamente complejos."
    DIVERGENCIA = "Los cálculos se descontrolaron y se alejaron por completo de una solución real."

    # === 4. RESTRICCIONES DE COMPATIBILIDAD INTERNA ===
    REQUIERE_OTRO_METODO = "El procedimiento actual no es capaz de resolver este tipo de restricciones."

    # === 5. ERRORES DE CONTROL Y ENTRADA ===
    ERROR_VALIDACION_ENTRADA = "Los datos ingresados están mal escritos, incompletos o son inconsistentes."
    ERROR_SISTEMA_INTERNO = "Ocurrió un fallo inesperado dentro del motor del programa."