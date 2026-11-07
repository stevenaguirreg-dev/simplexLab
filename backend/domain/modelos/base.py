"""Modelo base de un problema de programación lineal ya validado."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from fractions import Fraction
from typing import List

from ..texto import SIMBOLOS, expresion_lineal


@dataclass
class Restriccion:
    coeficientes: List[Fraction]
    relacion: str  # "<=", ">=" o "="
    rhs: Fraction


class ModeloPL(ABC):
    """Problema: Max/Min c·x sujeto a restricciones, con x >= 0.

    Las subclases fijan el número de variables (2 o 3) y deciden si el
    método gráfico aplica.
    """

    NUM_VARIABLES = 0

    def __init__(self, sentido, c, restricciones):
        self.sentido = sentido  # "max" o "min"
        self.c = list(c)
        self.restricciones = list(restricciones)
        self.nombres = [f"x{j + 1}" for j in range(self.NUM_VARIABLES)]

    @property
    def num_variables(self):
        return self.NUM_VARIABLES

    @property
    def num_restricciones(self):
        return len(self.restricciones)

    @property
    @abstractmethod
    def puede_graficar(self):
        """True solo si el problema tiene dos variables."""

    @abstractmethod
    def analisis_grafico(self, contexto):
        """Datos para el método gráfico, o el aviso de que no aplica."""

    def texto_objetivo(self):
        palabra = "Max" if self.sentido == "max" else "Min"
        return f"{palabra} Z = {expresion_lineal(self.c, self.nombres)}"

    def texto_restricciones(self):
        return [
            f"{expresion_lineal(r.coeficientes, self.nombres)} {SIMBOLOS[r.relacion]} {r.rhs}"
            for r in self.restricciones
        ]
