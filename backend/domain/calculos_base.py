"""Cantidades de una base dada (B^-1, X_B, multiplicadores y costos reducidos).

Lo usan la sensibilidad y los casos especiales, así no dependen del método
con el que se resolvió. Las artificiales se toman con costo 0 (solo importan
si quedó alguna en la base con valor 0).
"""
from fractions import Fraction

from .algebra import inversa, multiplicar_matriz_vector


class EstadoBase:
    def __init__(self, forma, base):
        self.forma = forma
        self.base = list(base)
        m, N = forma.m, forma.N
        B = [[forma.A[i][j] for j in self.base] for i in range(m)]
        self.B_inv = inversa(B)
        self.xb = multiplicar_matriz_vector(self.B_inv, forma.b)
        c = forma.costos_reales()
        cb = [c[j] for j in self.base]
        self.y = [sum((cb[i] * self.B_inv[i][k] for i in range(m)), Fraction(0)) for k in range(m)]
        self.d = [
            None if forma.es_artificial(j)
            else sum((self.y[k] * forma.A[k][j] for k in range(m)), Fraction(0)) - c[j]
            for j in range(N)
        ]

    def columna(self, j):
        """B^-1 a_j: la columna de la variable j vista desde la base."""
        return multiplicar_matriz_vector(self.B_inv, [self.forma.A[k][j] for k in range(self.forma.m)])
