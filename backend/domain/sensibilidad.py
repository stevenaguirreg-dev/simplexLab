"""Análisis de sensibilidad a partir de la base óptima.

 * Precio sombra de la restricción i: cuánto cambia Z por cada unidad extra de b_i.
 * Costo reducido de x_j: cuánto empeora Z por cada unidad que se obligue a entrar a x_j.
 * Rango de c_j: valores de c_j para los que la base óptima no cambia.
 * Rango de b_i: valores de b_i para los que la base óptima sigue siendo factible.
Las fórmulas son las de las clases 11 y 12 (B^-1, C_B B^-1).
"""
from fractions import Fraction

from .calculos_base import EstadoBase
from .numeros import numero_final, numero_final_o_nulo


def _mas_restrictivo_inferior(actual, candidato):
    return candidato if actual is None else max(actual, candidato)


def _mas_restrictivo_superior(actual, candidato):
    return candidato if actual is None else min(actual, candidato)


def analizar_sensibilidad(modelo, forma, base_final):
    est = EstadoBase(forma, base_final)
    sigma = 1 if modelo.sentido == "max" else -1
    n, m = forma.n_original, forma.m
    base = list(base_final)
    advertencias = []
    if any(forma.es_artificial(j) for j in base):
        advertencias.append(
            "Una variable artificial quedó en la base con valor 0 (restricción redundante); "
            "los rangos pueden ser más estrechos de lo habitual."
        )

    precios = []
    for i in range(m):
        signo = -1 if forma.filas_volteadas[i] else 1
        precios.append({"restriccion": i + 1, "valor": numero_final(sigma * signo * est.y[i])})

    costos = [
        {"variable": forma.nombres[j], "valor": numero_final(est.d[j]), "basica": j in base}
        for j in range(n)
    ]

    rangos_c = []
    for j in range(n):
        c_actual = modelo.c[j]
        if j not in base:
            d = est.d[j]
            minimo, maximo = (None, c_actual + d) if modelo.sentido == "max" else (c_actual - d, None)
        else:
            r = base.index(j)
            bajo = alto = None
            for k in range(forma.N):
                if k in base or forma.es_artificial(k):
                    continue
                alfa = est.columna(k)[r]
                if alfa > 0:
                    bajo = _mas_restrictivo_inferior(bajo, -est.d[k] / alfa)
                elif alfa < 0:
                    alto = _mas_restrictivo_superior(alto, -est.d[k] / alfa)
            if modelo.sentido == "max":
                delta_min, delta_max = bajo, alto
            else:
                delta_min = None if alto is None else -alto
                delta_max = None if bajo is None else -bajo
            minimo = None if delta_min is None else c_actual + delta_min
            maximo = None if delta_max is None else c_actual + delta_max
        rangos_c.append({
            "variable": forma.nombres[j],
            "actual": numero_final(c_actual),
            "minimo": numero_final_o_nulo(minimo),
            "maximo": numero_final_o_nulo(maximo),
            "basica": j in base,
        })

    rangos_b = []
    for i in range(m):
        signo = -1 if forma.filas_volteadas[i] else 1
        bajo = alto = None
        colapsa = False
        for k, jb in enumerate(base):
            g = signo * est.B_inv[k][i]
            if forma.es_artificial(jb):
                if g != 0:
                    colapsa = True
                continue
            if g > 0:
                bajo = _mas_restrictivo_inferior(bajo, -est.xb[k] / g)
            elif g < 0:
                alto = _mas_restrictivo_superior(alto, -est.xb[k] / g)
        b_actual = modelo.restricciones[i].rhs
        if colapsa:
            bajo = alto = Fraction(0)
        rangos_b.append({
            "restriccion": i + 1,
            "actual": numero_final(b_actual),
            "minimo": numero_final_o_nulo(None if bajo is None else b_actual + bajo),
            "maximo": numero_final_o_nulo(None if alto is None else b_actual + alto),
        })

    return {
        "precios_sombra": precios,
        "costos_reducidos": costos,
        "rangos_coeficientes": rangos_c,
        "rangos_lado_derecho": rangos_b,
        "advertencias": advertencias,
    }
