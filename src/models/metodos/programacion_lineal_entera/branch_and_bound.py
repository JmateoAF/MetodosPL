# src/models/metodos/programacion_lineal_entera/branch_and_bound.py

from fractions import Fraction
import math
from typing import List, Optional, Tuple, Union

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.models.entity.programacion_lineal.respuesta import RespuestaSciPyPL, RespuestaTabularPL
from src.models.entity.programacion_lineal_entera.enums import TipoVariable
from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE
from src.models.entity.programacion_lineal_entera.respuesta import (
    RespuestaBranchAndBound,
    NodoBranchAndBound,
    RamificacionVariable,
)

# Importar resolutores continuos de base
from src.models.metodos.programacion_lineal_basica.resolucion_rapida import ResolutorGeneral
from src.models.metodos.programacion_lineal_basica.simplex import SolucionadorSimplex
from src.models.metodos.programacion_lineal_basica.dos_fases import SolucionadorDosFases
from src.models.metodos.programacion_lineal_basica.m_grande import SolucionadorGranM


class SolucionadorBranchAndBound:
    """
    Solucionador de Programación Lineal Entera (PLE) y Mixta (MILP)
    utilizando el algoritmo de Ramificación y Acotamiento (Branch and Bound).
    """

    def __init__(self, metodo_lineal: Optional[int] = None) -> None:
        """
        Inicializa el solucionador.
        metodo_lineal:
            1 -> ResolutorGeneral (SciPy)
            2 -> SolucionadorSimplex (Tabular standard)
            3 -> SolucionadorGranM (Tabular Big M)
            4 -> SolucionadorDosFases (Tabular Two Phases)
            None -> Auto-detectar
        """
        self.metodo_lineal = metodo_lineal

    def resolver(self, problema: ProblemaPLE) -> RespuestaBranchAndBound:
        # 1. Analizar el nodo raíz para elegir el algoritmo continuo adecuado y mantenerlo
        solver = self._elegir_solver(problema)

        # 2. Inicializar cotas L y U
        # L[j] = 0, U[j] = 1 si es binaria, si no U[j] = None (infinito)
        L_inicial: List[Union[Fraction, float]] = []
        U_inicial: List[Optional[Union[Fraction, float]]] = []

        is_float = self._tiene_float(problema)

        for tipo in problema.tipos_variables:
            if tipo == TipoVariable.BINARIA:
                L_inicial.append(float(0.0) if is_float else Fraction(0))
                U_inicial.append(float(1.0) if is_float else Fraction(1))
            else:
                L_inicial.append(float(0.0) if is_float else Fraction(0))
                U_inicial.append(None)

        # 3. Inicializar variables del árbol de exploración
        arbol_nodos: List[NodoBranchAndBound] = []
        z_optimo: Optional[Union[Fraction, float]] = None
        x_optimo: Optional[List[Union[Fraction, float]]] = None

        # Pila para DFS: cada elemento es (id_nodo, id_padre, ramificacion, L, U)
        stack = [(1, None, None, L_inicial, U_inicial)]
        id_counter = 1

        es_max = (problema.tipo == TipoOptimizacion.MAX)

        while stack:
            id_nodo, id_padre, ramificacion, L, U = stack.pop()

            # Verificar si hay contradicción de cotas inmediata
            inviable_cotas = False
            for j in range(len(L)):
                uj = U[j]
                if uj is not None and uj < L[j]:
                    inviable_cotas = True
                    break

            if inviable_cotas:
                arbol_nodos.append(NodoBranchAndBound(
                    id_nodo=id_nodo,
                    id_padre=id_padre,
                    ramificacion=ramificacion,
                    z_local=None,
                    variables_locales=None,
                    estado_nodo=EstadoProblema.INVIABLE,
                    mensaje="Podado por contradicción de cotas (U < L)"
                ))
                continue

            # Construir subproblema continuo usando variable shifting
            sub_problema = self._construir_subproblema(problema, L, U)

            # Resolver relajación continua
            estado, z_relax, x_relax_shifted = self._resolver_relajacion(solver, sub_problema)

            if estado != EstadoProblema.OPTIMO:
                # Si el nodo raíz es inviable o no acotado, devolvemos ese estado
                if id_nodo == 1:
                    return RespuestaBranchAndBound(
                        estado=estado,
                        mensaje=estado.value,
                        z_optimo=None,
                        variables_decision=None,
                        arbol_nodos=[NodoBranchAndBound(
                            id_nodo=1,
                            id_padre=None,
                            ramificacion=None,
                            z_local=None,
                            variables_locales=None,
                            estado_nodo=estado,
                            mensaje=f"Relaxación de la raíz no es óptima: {estado.value}"
                        )]
                    )
                arbol_nodos.append(NodoBranchAndBound(
                    id_nodo=id_nodo,
                    id_padre=id_padre,
                    ramificacion=ramificacion,
                    z_local=None,
                    variables_locales=None,
                    estado_nodo=estado,
                    mensaje=f"Podado por relajación no óptima: {estado.value}"
                ))
                continue

            # Reconstruir solución real: X_j = Y_j + L_j
            x_relax = [x_relax_shifted[j] + L[j] for j in range(len(L))]
            # El valor real de Z es Z_relax + sum(c_j * L_j)
            const_shift = sum(problema.objetivo[j] * L[j] for j in range(len(L)))
            z_real = z_relax + const_shift

            # Pruning por cota
            if z_optimo is not None:
                if es_max and z_real <= z_optimo:
                    arbol_nodos.append(NodoBranchAndBound(
                        id_nodo=id_nodo,
                        id_padre=id_padre,
                        ramificacion=ramificacion,
                        z_local=z_real,
                        variables_locales=x_relax,
                        estado_nodo=EstadoProblema.OPTIMO,
                        mensaje=f"Podado por cota (Z={z_real} <= Z_best={z_optimo})"
                    ))
                    continue
                elif not es_max and z_real >= z_optimo:
                    arbol_nodos.append(NodoBranchAndBound(
                        id_nodo=id_nodo,
                        id_padre=id_padre,
                        ramificacion=ramificacion,
                        z_local=z_real,
                        variables_locales=x_relax,
                        estado_nodo=EstadoProblema.OPTIMO,
                        mensaje=f"Podado por cota (Z={z_real} >= Z_best={z_optimo})"
                    ))
                    continue

            # Verificar factibilidad entera
            idx_frac = self._obtener_variable_fraccionaria(x_relax, problema.tipos_variables)

            if idx_frac is None:
                # Solución entera factible encontrada
                z_optimo = z_real
                x_optimo = x_relax
                arbol_nodos.append(NodoBranchAndBound(
                    id_nodo=id_nodo,
                    id_padre=id_padre,
                    ramificacion=ramificacion,
                    z_local=z_real,
                    variables_locales=x_relax,
                    estado_nodo=EstadoProblema.OPTIMO,
                    mensaje=f"Solución entera factible (Z={z_real})"
                ))
            else:
                # Ramificar en variable idx_frac
                val_frac = x_relax[idx_frac]
                floor_val = math.floor(float(val_frac))
                ceil_val = math.ceil(float(val_frac))

                if is_float:
                    floor_val = float(floor_val)
                    ceil_val = float(ceil_val)
                else:
                    floor_val = Fraction(floor_val)
                    ceil_val = Fraction(ceil_val)

                # Registrar nodo actual de ramificación
                arbol_nodos.append(NodoBranchAndBound(
                    id_nodo=id_nodo,
                    id_padre=id_padre,
                    ramificacion=ramificacion,
                    z_local=z_real,
                    variables_locales=x_relax,
                    estado_nodo=EstadoProblema.OPTIMO,
                    mensaje=f"Ramificación en X{idx_frac + 1} = {val_frac}"
                ))

                # Crear hijos
                id_counter += 1
                id_hijo_der = id_counter
                L_der = list(L)
                U_der = list(U)
                L_der[idx_frac] = max(L_der[idx_frac], ceil_val)
                ram_der = RamificacionVariable(idx_frac, ceil_val, False)

                id_counter += 1
                id_hijo_izq = id_counter
                L_izq = list(L)
                U_izq = list(U)
                U_izq[idx_frac] = min(U_izq[idx_frac], floor_val) if U_izq[idx_frac] is not None else floor_val
                ram_izq = RamificacionVariable(idx_frac, floor_val, True)

                # Empujar a la pila (izq primero, der después, o viceversa)
                stack.append((id_hijo_der, id_nodo, ram_der, L_der, U_der))
                stack.append((id_hijo_izq, id_nodo, ram_izq, L_izq, U_izq))

        if z_optimo is None:
            return RespuestaBranchAndBound(
                estado=EstadoProblema.INVIABLE,
                mensaje=EstadoProblema.INVIABLE.value,
                z_optimo=None,
                variables_decision=None,
                arbol_nodos=arbol_nodos
            )

        return RespuestaBranchAndBound(
            estado=EstadoProblema.OPTIMO,
            mensaje=EstadoProblema.OPTIMO.value,
            z_optimo=z_optimo,
            variables_decision=x_optimo,
            arbol_nodos=arbol_nodos
        )

    def _tiene_float(self, problema: ProblemaPLE) -> bool:
        if any(isinstance(c, float) for c in problema.objetivo):
            return True
        for r in problema.restricciones:
            if any(isinstance(c, float) for c in r.coeficientes) or isinstance(r.rhs, float):
                return True
        return False

    def _elegir_solver(self, problema: ProblemaPLE):
        # Si el usuario especificó una opción de método lineal en el constructor, la respetamos
        if self.metodo_lineal == 1:
            return ResolutorGeneral()
        elif self.metodo_lineal == 2:
            return SolucionadorSimplex()
        elif self.metodo_lineal == 3:
            return SolucionadorGranM()
        elif self.metodo_lineal == 4:
            return SolucionadorDosFases()

        # Si no, autodetectamos el solver
        if self._tiene_float(problema):
            return ResolutorGeneral()

        # Si hay restricciones con signo >= o ==, no podemos usar Simplex clásico directo
        tiene_ge_eq = False
        for r in problema.restricciones:
            if r.signo in (SignoRestriccion.MAYOR_IGUAL, SignoRestriccion.IGUAL):
                tiene_ge_eq = True
                break

        if tiene_ge_eq:
            return SolucionadorDosFases()
        else:
            return SolucionadorSimplex()

    def _resolver_relajacion(self, solver, problem_sub: ProblemaPL) -> Tuple[EstadoProblema, Optional[Union[Fraction, float]], Optional[List[Union[Fraction, float]]]]:
        res = solver.resolver(problem_sub)
        if isinstance(res, RespuestaSciPyPL):
            if res.estado == EstadoProblema.OPTIMO and res.x is not None and res.fun is not None:
                return EstadoProblema.OPTIMO, res.fun, res.x
            else:
                return res.estado, None, None
        elif isinstance(res, RespuestaTabularPL):
            if res.estado == EstadoProblema.OPTIMO and res.variables_decision is not None and res.z_optimo is not None:
                return EstadoProblema.OPTIMO, res.z_optimo, res.variables_decision
            else:
                return res.estado, None, None
        else:
            raise TypeError("Respuesta del solucionador continuo no soportada.")

    def _construir_subproblema(self, problema: ProblemaPLE, L: List[Union[Fraction, float]], U: List[Optional[Union[Fraction, float]]]) -> ProblemaPL:
        is_float = self._tiene_float(problema)
        restricciones_nuevas = []

        # 1. Transformar restricciones existentes usando variable shifting
        # sum(a_k * X_k) <= b => sum(a_k * Y_k) <= b - sum(a_k * L_k)
        for r in problema.restricciones:
            shift_term = sum(r.coeficientes[k] * L[k] for k in range(len(L)))
            new_rhs = r.rhs - shift_term
            restricciones_nuevas.append(Restriccion(
                coeficientes=list(r.coeficientes),
                signo=r.signo,
                rhs=new_rhs
            ))

        # 2. Agregar restricciones para los límites superiores activos U[k]
        # Y_k <= U_k - L_k
        for k, uk in enumerate(U):
            if uk is not None:
                coefs = [float(0.0) if is_float else Fraction(0)] * len(L)
                coefs[k] = float(1.0) if is_float else Fraction(1)
                rhs_val = uk - L[k]
                restricciones_nuevas.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=rhs_val
                ))

        return ProblemaPL(
            tipo=problema.tipo,
            objetivo=list(problema.objetivo),
            restricciones=restricciones_nuevas
        )

    def _obtener_variable_fraccionaria(self, x: List[Union[Fraction, float]], tipos: List[TipoVariable]) -> Optional[int]:
        for j, val in enumerate(x):
            if tipos[j] in (TipoVariable.ENTERA, TipoVariable.BINARIA):
                # Verificar si es fraccionaria
                if isinstance(val, Fraction):
                    if val.denominator != 1:
                        return j
                else:
                    # float precision checking
                    if abs(val - round(val)) > 1e-6:
                        return j
        return None
