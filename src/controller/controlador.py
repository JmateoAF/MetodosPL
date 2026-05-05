from src.models.dos_fases import SolucionadorDosFases
from src.models.m_grande import SolucionadorGranM
from src.models.resolucion_rapida import ResolutorGeneral
from src.models.simplex import SolucionadorSimplex

class Controlador:

    _solver_casos_general = ResolutorGeneral()
    _solver_simplex = SolucionadorSimplex()
    _solver_M_grande = SolucionadorGranM()
    _solver_dos_fases = SolucionadorDosFases()

    def __init__(self):
        pass

    def resolver_LP(self, datos_entrada : dict, opcion : int) -> dict:
        match opcion:
            case 1:
                return self._solver_casos_general.resolver(datos_entrada)
            case 2:
                return self._solver_simplex.resolver(datos_entrada)
            case 3:
                return self._solver_M_grande.resolver(datos_entrada)
            case 4:
                return self._solver_dos_fases.resolver(datos_entrada)
            case _:
                return None
