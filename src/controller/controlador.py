from src.models.dos_fases import SolucionadorDosFases
from src.models.historial_de_problemas import HistorialDeProblemas
from src.models.m_grande import SolucionadorGranM
from src.models.resolucion_rapida import ResolutorGeneral
from src.models.simplex import SolucionadorSimplex

class Controlador:

    _solver_casos_general = ResolutorGeneral()
    _solver_simplex = SolucionadorSimplex()
    _solver_M_grande = SolucionadorGranM()
    _solver_dos_fases = SolucionadorDosFases()
    _historial_de_problema = HistorialDeProblemas()

    def __init__(self) -> None:
        pass

    """
    Se usa la opcion : int, para selecionar el metodo a usar para resolver el problema
    1: metodo general
    2: metodo simplex
    3: metodo de la M grande
    4: metodo de las dos fases
    """
    def resolver_LP(self, datos_entrada : dict, opcion : int) -> dict | None:
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

    """
    Se usa la opcion para elegir que metodo usar
    1: metodo para guardar un problema
    2: metodo para obtener un problema a partir de su indice en el historial
    3: metodo para eliminar un problema a partir de su indice
    """
    def operar_problema(self, datos_entrada : dict, opcion : int, indice = 0) -> dict | None:
        match opcion:
            case 1:
                return self._historial_de_problema.ingresar_problema(datos_entrada)
            case 2:
                return self._historial_de_problema.obtener_problemas(indice)
            case 3:
                return self._historial_de_problema.eliminar_problema(indice)
            case _:
                return None

    # Metodo para devolver todo el historial compelto
    def obtener_historial_de_problema(self) -> list[dict]:
        return self._historial_de_problema.obtener_historial_de_problemas()
