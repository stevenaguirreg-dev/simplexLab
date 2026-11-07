"""Simplex revisado: solo se mantiene B^-1 y se calculan costos y columnas cuando se necesitan.

Formulas (las de la clase 11):
  X_B = B^-1 b          Z = C_B B^-1 b
  d_j = C_B B^-1 P_j - C_j          alfa = B^-1 P_j          theta = min(X_B / alfa)
"""
from fractions import Fraction

from ..algebra import identidad, inversa, multiplicar_matriz_vector
from ..numeros import GranM
from .base import ResolutorSimplex


class ResolutorRevisado(ResolutorSimplex):
    nombre = "revisado"

    def _iniciar(self):
        f = self.forma
        B = [[f.A[i][j] for j in self.base] for i in range(f.m)]
        self.B_inv = inversa(B) if f.m else identidad(0)

    def _y(self):
        """Multiplicadores y = C_B B^-1 (precios sombra del estado actual)."""
        f = self.forma
        cb = [f.c[j] for j in self.base]
        return [
            sum((cb[i] * self.B_inv[i][k] for i in range(f.m)), start=GranM(0))
            for k in range(f.m)
        ]

    def _costos_reducidos(self):
        f = self.forma
        y = self._y()
        return [
            sum((y[k] * f.A[k][j] for k in range(f.m)), start=GranM(0)) - f.c[j] for j in range(f.N)
        ]

    def _columna(self, j):
        f = self.forma
        return multiplicar_matriz_vector(self.B_inv, [f.A[k][j] for k in range(f.m)])

    def _xb(self):
        return multiplicar_matriz_vector(self.B_inv, self.forma.b)

    def _valor_z(self):
        y = self._y()
        f = self.forma
        return sum((y[k] * f.b[k] for k in range(f.m)), start=GranM(0))

    def _pivotar(self, fila, columna):
        alfa = self._columna(columna)
        pivote = alfa[fila]
        self.B_inv[fila] = [v / pivote for v in self.B_inv[fila]]
        for i in range(len(self.B_inv)):
            if i != fila and alfa[i] != 0:
                self.B_inv[i] = [v - alfa[i] * w for v, w in zip(self.B_inv[i], self.B_inv[fila])]
        self.base[fila] = columna

    def _instantanea(self):
        f = self.forma
        d = self._costos_reducidos()
        return {
            "tipo": "revisado",
            "etiqueta_z": f.etiqueta_z,
            "base": [f.nombres[j] for j in self.base],
            "B_inv": [list(fila) for fila in self.B_inv],
            "xb": self._xb(),
            "y": self._y(),
            "z": self._valor_z(),
            "costos_reducidos": [
                {"variable": f.nombres[j], "valor": d[j], "basica": j in self.base, "artificial": f.es_artificial(j)}
                for j in range(f.N)
            ],
        }
