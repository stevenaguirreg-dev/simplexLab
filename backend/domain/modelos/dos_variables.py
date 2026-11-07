"""Modelo con dos variables: admite método gráfico."""
from .base import ModeloPL
from ..grafico import AnalizadorGrafico


class ModeloDosVariables(ModeloPL):
    NUM_VARIABLES = 2

    @property
    def puede_graficar(self):
        return True

    def analisis_grafico(self, contexto):
        return AnalizadorGrafico(self).calcular(contexto)
