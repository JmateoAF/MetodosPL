# src/models/entity/programacion_lineal_entera/enums.py
from enum import Enum, unique

@unique
class TipoVariable(Enum):
    CONTINUA = "CONTINUA"
    ENTERA = "ENTERA"
    BINARIA = "BINARIA"


@unique
class OperadorLogico(Enum):
    """
    Operadores del álgebra booleana permitidos para modelar restricciones lógicas.
    Mapea de forma finita y estricta las relaciones proposicionales entre variables binarias.
    """
    # 1. NEGACIÓN (NOT): X_origen = 1 - X_destino
    NEGACION = "NEGACION"
    
    # 2. CONJUNCIÓN (AND): Exige que todas las variables involucradas sean 1
    CONJUNCION = "CONJUNCION"
    
    # 3. DISYUNCIÓN INCLUSIVA (OR): Al menos una variable debe ser 1 (pueden ser más)
    DISYUNCION = "DISYUNCION"
    
    # 4. EXCLUSIÓN MUTUA (XOR): Exactamente una variable debe ser 1 (nunca ambas)
    EXCLUSION_MUTUA = "EXCLUSION_MUTUA"
    
    # 5. CONDICIONAL (IMPLICA): Si ocurre el origen, obliga la ocurrencia del destino
    IMPLICACION = "IMPLICACION"
    
    # 6. BICONDICIONAL (EQUIVALENTE): Co-requisito. Ambos ocurren o ninguno ocurre
    EQUIVALENCIA = "EQUIVALENCIA"


@unique
class OperadorMGrande(Enum):
    """
    Operadores lógicos avanzados que requieren variables binarias artificiales 
    de control e interceptación mediante la M Grande de modelado.
    """
    # 1. CONJUNCIÓN DE RESTRICCIONES (AND): Todas las inecuaciones del bloque deben cumplirse simultáneamente
    CONJUNCION_RESTRICCIONES = "CONJUNCION_RESTRICCIONES"

    # 2. O entre restricciones algebraicas completas (Disyunción)
    DISYUNCION_RESTRICCIONES = "DISYUNCION_RESTRICCIONES"
    
    # 3. Activar exactamente K restricciones de un paquete de N opciones
    SELECCION_K_DE_N = "SELECCION_K_DE_N"
    
    # 4. Costo fijo o activación de umbral cuando una variable continua es > 0
    ACTIVACION_UMBRAL = "ACTIVACION_UMBRAL"
    
    # 5. Condicional compuesto: SI ocurre la ecuación A, ENTONCES se aplica la ecuación B
    CONDICIONAL_COMPUESTO = "CONDICIONAL_COMPUESTO"
    
    # 6. Variable continua o entera acotada a valores aislados específicos (Tramos)
    VALORES_DISJUNTOS = "VALORES_DISJUNTOS"