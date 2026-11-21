"""Modelo de un problema de programación lineal ya validado, con n variables."""
from dataclasses import dataclass
from fractions import Fraction
from typing import List

from ..grafico import AnalizadorGrafico
from ..texto import SIMBOLOS, expresion_lineal


@dataclass
class Restriccion:
    coeficientes: List[Fraction]
    relacion: str  # "<=", ">=" o "="
    rhs: Fraction


class ModeloPL:
    """Problema: Max/Min c·x sujeto a restricciones, con x >= 0 y n variables (n >= 2).

    El método gráfico solo aplica cuando n = 2.
    """

    def __init__(self, sentido, c, restricciones):
        self.sentido = sentido  # "max" o "min"
        self.c = list(c)
        self.restricciones = list(restricciones)
        self.nombres = [f"x{j + 1}" for j in range(len(self.c))]

    @property
    def num_variables(self):
        return len(self.c)

    @property
    def num_restricciones(self):
        return len(self.restricciones)

    @property
    def puede_graficar(self):
        """True solo si el problema tiene dos variables."""
        return self.num_variables == 2

    def analisis_grafico(self, contexto):
        """Datos para el método gráfico, o el aviso de que no aplica."""
        if not self.puede_graficar:
            return {
                "aplica": False,
                "mensaje": "El método gráfico no aplica: el problema tiene más de dos variables.",
            }
        return AnalizadorGrafico(self).calcular(contexto)

    def texto_objetivo(self):
        palabra = "Max" if self.sentido == "max" else "Min"
        return f"{palabra} Z = {expresion_lineal(self.c, self.nombres)}"

    def texto_restricciones(self):
        return [
            f"{expresion_lineal(r.coeficientes, self.nombres)} {SIMBOLOS[r.relacion]} {r.rhs}"
            for r in self.restricciones
        ]
