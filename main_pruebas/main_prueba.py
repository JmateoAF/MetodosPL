from src.controller.controlador import Controlador
from ui.view_prueba import View

if __name__ == "__main__":
    controlador = Controlador()
    vista = View(controlador)
    vista.prueba_rapida()