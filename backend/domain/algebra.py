"""Álgebra lineal mínima con fracciones exactas (sin numpy, para no perder exactitud)."""
from fractions import Fraction

from .errores import MatrizSingularError


def identidad(n):
    return [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]


def multiplicar_matriz_vector(matriz, vector):
    return [sum((fila[k] * vector[k] for k in range(len(vector))), Fraction(0)) for fila in matriz]


def inversa(matriz):
    """Inversa por Gauss-Jordan. Lanza MatrizSingularError si no existe."""
    n = len(matriz)
    aumentada = [list(map(Fraction, fila)) + identidad(n)[i] for i, fila in enumerate(matriz)]
    for col in range(n):
        pivote = next((r for r in range(col, n) if aumentada[r][col] != 0), None)
        if pivote is None:
            raise MatrizSingularError("La matriz de la base no tiene inversa.")
        aumentada[col], aumentada[pivote] = aumentada[pivote], aumentada[col]
        p = aumentada[col][col]
        aumentada[col] = [v / p for v in aumentada[col]]
        for r in range(n):
            if r != col and aumentada[r][col] != 0:
                f = aumentada[r][col]
                aumentada[r] = [v - f * w for v, w in zip(aumentada[r], aumentada[col])]
    return [fila[n:] for fila in aumentada]
