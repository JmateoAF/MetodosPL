# src/utils/perser.py
"""
parser.py
=========
Módulo encargado del análisis sintáctico (parsing) y convalidación textual
para la creación de modelos de Programación Lineal a partir de strings.

Soporta dos variantes de entrada:
    1. Formato Natural: Expresiones algebraicas legibles (ej. "Max Z = 3x1 - x2").
    2. Formato por Coeficientes (CSV): Secuencias numéricas separadas por comas.

Garantiza el retorno exclusivo de entidades inmutables del dominio (POO).
Autor: Utilities Parser Module — MVC Linear Optimizer
"""

import re
from fractions import Fraction
from typing import List

# Importaciones estrictas de las entidades y enumerados de dominio
from src.models.entity.programacion_lineal.enums import TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion, Numerico


class MotorParsing:
    """
    Analizador basado en expresiones regulares para transformar entradas de la UI
    en estructuras matemáticas fuertemente tipadas y validadas.
    """

    @classmethod
    def _parsear_valor_fraccionario(cls, texto_numero: str) -> Fraction:
        """Convierte una subcadena en un objeto Fraction exacto."""
        texto_limpio = texto_numero.strip().replace(" ", "")
        if not texto_limpio or texto_limpio == "+":
            return Fraction(1, 1)
        if texto_limpio == "-":
            return Fraction(-1, 1)
        
        try:
            if "/" in texto_limpio:
                num, den = texto_limpio.split("/", 1)
                return Fraction(int(num), int(den))
            if "." in texto_limpio:
                return Fraction(float(texto_limpio)).limit_denominator()
            return Fraction(int(texto_limpio), 1)
        except (ValueError, ZeroDivisionError) as err:
            raise ValueError(f"Formato numérico inválido: '{texto_numero}'. Detalles: {err}")

    @classmethod
    def csv_a_entidades(cls, texto_objetivo: str, lineas_restricciones: List[str]) -> ProblemaPL:
        """
        Interpreta el ingreso por coeficientes planos separados por comas.
        
        Ejemplo Objetivo: "Max, 3, 5, -2"
        Ejemplo Restricción: "1, 0, 2, <=, 10"
        """
        # 1. Procesar función objetivo
        partes_obj = [p.strip() for p in texto_objetivo.split(",") if p.strip()]
        if not partes_obj:
            raise ValueError("El campo de la función objetivo CSV está vacío.")
        
        try:
            tipo_enum = TipoOptimizacion(partes_obj[0].upper())
        except ValueError:
            raise ValueError(f"El tipo de optimización CSV debe ser MAX o MIN. Recibido: '{partes_obj[0]}'")

        objetivo_coefs: List[Numerico] = [
            cls._parsear_valor_fraccionario(c) for c in partes_obj[1:]
        ]
        
        if not objetivo_coefs:
            raise ValueError("La función objetivo CSV no contiene coeficientes numéricos.")

        # 2. Procesar restricciones lineales
        lista_restricciones: List[Restriccion] = []
        
        for idx, linea in enumerate(lineas_restricciones):
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue

            partes_res = [p.strip() for p in linea_limpia.split(",")]
            if len(partes_res) < 3:
                raise ValueError(f"La restricción CSV en la línea {idx + 1} está incompleta.")

            # El signo y el RHS se ubican en las últimas posiciones
            rhs_str = partes_res[-1]
            signo_str = partes_res[-2]
            coefs_str = partes_res[:-2]

            try:
                signo_enum = SignoRestriccion(signo_str)
            except ValueError:
                raise ValueError(
                    f"Signo inválido '{signo_str}' en la línea {idx + 1}. "
                    f"Use exclusivamente: '<=', '>=' o '=='."
                )

            coeficientes_res: List[Numerico] = [
                cls._parsear_valor_fraccionario(c) for c in coefs_str
            ]
            rhs_valor = cls._parsear_valor_fraccionario(rhs_str)

            # Instanciación nativa de la entidad inmutable
            restriccion_entidad = Restriccion(
                coeficientes=coeficientes_res,
                signo=signo_enum,
                rhs=rhs_valor
            )
            lista_restricciones.append(restriccion_entidad)

        # Retorna el objeto unificado ejecutando sus validaciones internas de constructor
        return ProblemaPL(
            tipo=tipo_enum,
            objetivo=objetivo_coefs,
            restricciones=lista_restricciones
        )

    @classmethod
    def natural_a_entidades(cls, texto_objetivo: str, lineas_restricciones: List[str]) -> ProblemaPL:
        """
        Interpreta ecuaciones algebraicas naturales mediante expresiones regulares masivas.
        Soporta coeficientes implícitos, espacios arbitrarios y desorden de variables.
        
        Ejemplo Objetivo: "Max Z = 3x1 + 5x2 - 2x3"
        Ejemplo Restricción: "1x1 + 3x3 <= 10"
        """
        # Expresión regular para capturar monomios: (signo/fracción)? (x|X) (número_índice)
        patron_monomio = re.compile(r"([+-]?(?:\d+(?:\.\d+)?(?:/\d+)?)?)[xX](\d+)")

        # 1. Parsear Función Objetivo Natural
        obj_limpio = texto_objetivo.strip().replace(" ", "")
        match_tipo = re.match(r"^(MAX|MIN)", obj_limpio, re.IGNORECASE)
        if not match_tipo:
            raise ValueError("La función objetivo natural debe iniciar con 'Max' o 'Min'.")
        
        tipo_enum = TipoOptimizacion(match_tipo.group(1).upper())

        # Remover encabezados decorativos clásicos como "Max Z =" o "Min f(x) ="
        cuerpo_objetivo = re.sub(r"^(MAX|MIN)[^=]*=", "", obj_limpio, flags=re.IGNORECASE)

        # Encontrar todas las variables presentes y registrar el índice más alto detectado
        monomios_obj = patron_monomio.findall(cuerpo_objetivo)
        if not monomios_obj:
            raise ValueError("No se detectaron variables válidas (ej. x1, x2) en la función objetivo.")

        max_indice_var = max(int(idx) for _, idx in monomios_obj)
        
        # Mapear el vector objetivo inicializado en cero para rellenar variables ausentes
        objetivo_coefs: list[Numerico] = [Fraction(0, 1)] * max_indice_var
        for coef_str, idx_str in monomios_obj:
            idx_pos = int(idx_str) - 1
            objetivo_coefs[idx_pos] = cls._parsear_valor_fraccionario(coef_str)

        # 2. Parsear Restricciones Naturales
        lista_restricciones: List[Restriccion] = []
        patron_signos = re.compile(r"(<=|>=|==)")

        for idx, linea in enumerate(lineas_restricciones):
            linea_limpia = linea.strip().replace(" ", "")
            if not linea_limpia:
                continue

            partes_ecuacion = patron_signos.split(linea_limpia)
            if len(partes_ecuacion) != 3:
                raise ValueError(f"Estructura algebraica incorrecta en la restricción línea {idx + 1}.")

            lado_izquierdo, signo_str, lado_derecho = partes_ecuacion

            try:
                signo_enum = SignoRestriccion(signo_str)
            except ValueError:
                raise ValueError(f"Signo de desigualdad inválido '{signo_str}' en la línea {idx + 1}.")

            rhs_valor = cls._parsear_valor_fraccionario(lado_derecho)

            # Extraer monomios del lado izquierdo de la restricción
            monomios_res = patron_monomio.findall(lado_izquierdo)
            coeficientes_res: list[Numerico] = [Fraction(0, 1)] * max_indice_var

            for coef_str, idx_str in monomios_res:
                idx_pos = int(idx_str) - 1
                # Evitar desbordamiento de índices si la restricción menciona una variable superior
                if idx_pos >= max_indice_var:
                    raise ValueError(
                        f"Error en restricción {idx + 1}: La variable 'X{idx_str}' "
                        f"supera la cantidad de variables declaradas en la función objetivo ({max_indice_var})."
                    )
                coeficientes_res[idx_pos] = cls._parsear_valor_fraccionario(coef_str)

            restriccion_entidad = Restriccion(
                coeficientes=coeficientes_res,
                signo=signo_enum,
                rhs=rhs_valor
            )
            lista_restricciones.append(restriccion_entidad)

        return ProblemaPL(
            tipo=tipo_enum,
            objetivo=objetivo_coefs,
            restricciones=lista_restricciones
        )
    