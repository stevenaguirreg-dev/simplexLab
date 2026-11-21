"""Método de la Gran M con tablero completo (el formato visto en clase)."""
from fractions import Fraction

from ..numeros import GranM
from .base import ResolutorSimplex


class ResolutorGranM(ResolutorSimplex):
    nombre = "gran_m"

    def _iniciar(self):
        f = self.forma
        self.T = [list(f.A[i]) + [f.b[i]] for i in range(f.m)]   # filas de restricciones (fracciones)
        y = [f.c[j] for j in self.base]                           # c_B (la base inicial es la identidad)
        self.z = [
            sum((y[i] * f.A[i][j] for i in range(f.m)), start=GranM(0)) - f.c[j] for j in range(f.N)
        ]
        self.z.append(sum((y[i] * f.b[i] for i in range(f.m)), start=GranM(0)))

    def _costos_reducidos(self):
        return self.z[:-1]

    def _columna(self, j):
        return [fila[j] for fila in self.T]

    def _xb(self):
        return [fila[-1] for fila in self.T]

    def _valor_z(self):
        return self.z[-1]

    def _pivotar(self, fila, columna):
        pivote = self.T[fila][columna]
        self.T[fila] = [v / pivote for v in self.T[fila]]
        for i in range(len(self.T)):
            if i != fila and self.T[i][columna] != 0:
                factor = self.T[i][columna]
                self.T[i] = [v - factor * w for v, w in zip(self.T[i], self.T[fila])]
        factor = self.z[columna]
        if factor != 0:
            self.z = [v - factor * w for v, w in zip(self.z, self.T[fila])]
        self.base[fila] = columna

    def _instantanea(self):
        f = self.forma
        return {
            "tipo": "tablero",
            "columnas": list(f.nombres) + ["LD"],
            "etiqueta_z": f.etiqueta_z,
            "fila_z": list(self.z),
            "filas": [
                {"variable_basica": f.nombres[self.base[i]], "valores": list(self.T[i])}
                for i in range(f.m)
            ],
        }
