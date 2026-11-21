"""Conversión del modelo a forma estándar aumentada (holguras, excesos y artificiales).

Reglas del curso:
  * Min Z se convierte en Max (-Z).
  * Si el lado derecho es negativo, se multiplica la restricción por -1 e invierte la desigualdad.
  * <=  suma una holgura s.
  * >=  resta un exceso e y suma una artificial a.
  * =   suma una artificial a.
Las artificiales entran a la función objetivo con coeficiente -M (método de la Gran M).
"""
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import List

from .numeros import GranM
from .texto import SIMBOLOS, expresion_lineal

ORIGINAL, HOLGURA, EXCESO, ARTIFICIAL = "original", "holgura", "exceso", "artificial"
INVERTIR = {"<=": ">=", ">=": "<=", "=": "="}


@dataclass
class FormaEstandar:
    sentido: str
    nombres: List[str]
    tipos: List[str]
    A: List[List[Fraction]]
    b: List[Fraction]
    c: List[GranM]            # costos de la forma Max (artificiales = -M)
    base_inicial: List[int]
    n_original: int
    filas_volteadas: List[bool]
    transformaciones: List[str] = field(default_factory=list)
    ecuaciones: List[str] = field(default_factory=list)
    objetivo_texto: str = ""
    etiqueta_z: str = "Z"

    @property
    def m(self):
        return len(self.b)

    @property
    def N(self):
        return len(self.nombres)

    def es_artificial(self, j):
        return self.tipos[j] == ARTIFICIAL

    def hay_artificiales(self):
        return any(t == ARTIFICIAL for t in self.tipos)

    def costos_reales(self):
        """Costos de la forma Max sin M (artificiales valen 0). Para sensibilidad."""
        return [Fraction(0) if self.es_artificial(j) else self.c[j].a for j in range(self.N)]

    def con_objetivo_cero(self):
        """Misma restricción, objetivo 0 (las artificiales siguen penalizadas). Sirve para probar factibilidad."""
        nuevos = [GranM(0, -1) if self.es_artificial(j) else GranM(0) for j in range(self.N)]
        return replace(self, c=nuevos)


def construir_forma_estandar(modelo):
    n = modelo.num_variables
    m = modelo.num_restricciones
    sentido = modelo.sentido
    transformaciones = []

    if sentido == "min":
        transformaciones.append("Minimizar Z equivale a maximizar -Z: se cambia el signo de los coeficientes de la función objetivo.")
        c_max = [-x for x in modelo.c]
    else:
        c_max = list(modelo.c)

    filas, relaciones, rhs, volteadas = [], [], [], []
    for i, r in enumerate(modelo.restricciones, start=1):
        coef, rel, lado, volteada = list(r.coeficientes), r.relacion, r.rhs, False
        if lado < 0:
            coef = [-x for x in coef]
            lado = -lado
            nueva = INVERTIR[rel]
            transformaciones.append(
                f"Restricción {i}: el lado derecho es negativo, se multiplica por -1 ({SIMBOLOS[rel]} pasa a {SIMBOLOS[nueva]})."
            )
            rel, volteada = nueva, True
        filas.append(coef)
        relaciones.append(rel)
        rhs.append(lado)
        volteadas.append(volteada)

    nombres = list(modelo.nombres)
    tipos = [ORIGINAL] * n
    columnas_extra = []   # (indice_fila, nombre, tipo, signo)
    for i, rel in enumerate(relaciones):
        if rel == "<=":
            columnas_extra.append((i, f"s{i + 1}", HOLGURA, 1))
            transformaciones.append(f"Restricción {i + 1} (≤): se suma la variable de holgura s{i + 1}.")
        elif rel == ">=":
            columnas_extra.append((i, f"e{i + 1}", EXCESO, -1))
            transformaciones.append(f"Restricción {i + 1} (≥): se resta la variable de exceso e{i + 1} y se suma la artificial a{i + 1}.")
        else:
            transformaciones.append(f"Restricción {i + 1} (=): se suma la artificial a{i + 1}.")
    artificiales = [(i, f"a{i + 1}") for i, rel in enumerate(relaciones) if rel in (">=", "=")]

    N = n + len(columnas_extra) + len(artificiales)
    A = [list(filas[i]) + [Fraction(0)] * (N - n) for i in range(m)]
    c = [GranM(x) for x in c_max] + [GranM(0)] * (N - n)
    base = [None] * m
    col = n
    for i, nombre, tipo, signo in columnas_extra:
        A[i][col] = Fraction(signo)
        nombres.append(nombre)
        tipos.append(tipo)
        if tipo == HOLGURA:
            base[i] = col
        col += 1
    for i, nombre in artificiales:
        A[i][col] = Fraction(1)
        nombres.append(nombre)
        tipos.append(ARTIFICIAL)
        c[col] = GranM(0, -1)
        base[i] = col
        col += 1

    ecuaciones = [f"{expresion_lineal(A[i], nombres)} = {rhs[i]}" for i in range(m)]
    etiqueta = "Z" if sentido == "max" else "-Z"
    objetivo = f"Max {etiqueta} = {expresion_lineal(c_max, modelo.nombres)}"
    for _, nombre in artificiales:
        objetivo += f" - M·{nombre}"
    return FormaEstandar(
        sentido=sentido,
        nombres=nombres,
        tipos=tipos,
        A=A,
        b=rhs,
        c=c,
        base_inicial=base,
        n_original=n,
        filas_volteadas=volteadas,
        transformaciones=transformaciones,
        ecuaciones=ecuaciones,
        objetivo_texto=objetivo,
        etiqueta_z=etiqueta,
    )
