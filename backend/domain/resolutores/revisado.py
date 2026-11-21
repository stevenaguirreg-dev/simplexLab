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
        # Entradas no nulas de cada columna de A: las de holgura, exceso y artificiales tienen una sola.
        self._no_ceros = [[(k, f.A[k][j]) for k in range(f.m) if f.A[k][j] != 0] for j in range(f.N)]
        self._y_memo = None

    def _columna_de(self, j):
        """B^-1 a_j aprovechando que a_j casi siempre tiene pocas entradas distintas de cero."""
        return [sum((fila[k] * a for k, a in self._no_ceros[j]), start=Fraction(0)) for fila in self.B_inv]

    def _y(self):
        """Multiplicadores y = C_B B^-1 (precios sombra del estado actual)."""
        if self._y_memo is None:   # se recalcula solo cuando cambia la base
            f = self.forma
            cb = [f.c[j] for j in self.base]
            self._y_memo = [
                sum((cb[i] * self.B_inv[i][k] for i in range(f.m)), start=GranM(0))
                for k in range(f.m)
            ]
        return self._y_memo

    def _costos_reducidos(self, y=None):
        f = self.forma
        y = self._y() if y is None else y
        return [
            sum((y[k] * f.A[k][j] for k in range(f.m)), start=GranM(0)) - f.c[j] for j in range(f.N)
        ]

    def _columna(self, j):
        return self._columna_de(j)

    def _xb(self):
        return multiplicar_matriz_vector(self.B_inv, self.forma.b)

    def _valor_z(self, y=None):
        y = self._y() if y is None else y
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
        self._y_memo = None

    def _instantanea(self):
        f = self.forma
        y = self._y()
        d = self._costos_reducidos(y)
        z = self._valor_z(y)
        xb = self._xb()
        # Tablero equivalente: cada fila i es (B^-1 A)_i | X_B_i. Se calcula con B^-1, sin pivotear el tablero.
        columnas = [self._columna(j) for j in range(f.N)]
        return {
            "tipo": "revisado",
            "columnas": list(f.nombres) + ["LD"],
            "etiqueta_z": f.etiqueta_z,
            "fila_z": [GranM(0) if j in self.base else d[j] for j in range(f.N)] + [z],
            "filas": [
                {
                    "variable_basica": f.nombres[self.base[i]],
                    "valores": [columnas[j][i] for j in range(f.N)] + [xb[i]],
                }
                for i in range(f.m)
            ],
            # Datos propios del método revisado (se muestran como detalle complementario)
            "base": [f.nombres[j] for j in self.base],
            "B_inv": [list(fila) for fila in self.B_inv],
            "xb": xb,
            "y": y,
            "z": z,
        }