from .base import ModeloPL, Restriccion
from .dos_variables import ModeloDosVariables
from .tres_variables import ModeloTresVariables


def crear_modelo(num_variables, sentido, c, restricciones):
    """Fábrica: elige el modelo según el número de variables."""
    clase = ModeloDosVariables if num_variables == 2 else ModeloTresVariables
    return clase(sentido, c, restricciones)
