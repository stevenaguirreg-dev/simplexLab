"""Modelo con tres variables: se resuelve con simplex, pero no se puede graficar en 2D."""
from .base import ModeloPL


class ModeloTresVariables(ModeloPL):
    NUM_VARIABLES = 3

    @property
    def puede_graficar(self):
        return False

    def analisis_grafico(self, contexto):
        return {
            "aplica": False,
            "mensaje": "El método gráfico no aplica: el problema tiene más de dos variables.",
        }
