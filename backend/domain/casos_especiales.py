"""Detección de casos sin solución única: degeneración y óptimos múltiples."""
from fractions import Fraction

from .calculos_base import EstadoBase
from .numeros import numero_final


def _punto_texto(valores):
    return "(" + ", ".join(str(v) for v in valores) + ")"


def detectar_casos_optimos(modelo, forma, resultado):
    """Analiza un resultado ÓPTIMO. Devuelve banderas, mensajes y vértices alternativos."""
    n = forma.n_original
    xb_por_variable = {j: resultado.x[j] for j in resultado.base}
    basicas_en_cero = [forma.nombres[j] for j, v in xb_por_variable.items() if v == 0]

    info = {
        "degenerado": bool(basicas_en_cero),
        "variables_basicas_en_cero": basicas_en_cero,
        "optimos_multiples": False,
        "rayo_optimo": False,
        "optimos_alternativos": [],
        "mensajes": [],
    }
    if basicas_en_cero:
        nombres = ", ".join(basicas_en_cero)
        info["mensajes"].append(
            f"Solución degenerada: la variable básica {nombres} vale 0 en el óptimo."
            if len(basicas_en_cero) == 1
            else f"Solución degenerada: las variables básicas {nombres} valen 0 en el óptimo."
        )

    est = EstadoBase(forma, resultado.base)
    actual = resultado.x[:n]
    encontrados = []
    for j in range(forma.N):
        if j in resultado.base or forma.es_artificial(j) or est.d[j] != 0:
            continue
        alfa = est.columna(j)
        razones = [est.xb[i] / alfa[i] for i in range(forma.m) if alfa[i] > 0]
        if not razones:
            info["rayo_optimo"] = True
            continue
        theta = min(razones)
        nuevo = [Fraction(0)] * forma.N
        for i, jb in enumerate(resultado.base):
            nuevo[jb] = est.xb[i] - theta * alfa[i]
        nuevo[j] = theta
        punto = nuevo[:n]
        if punto != actual and punto not in encontrados:
            encontrados.append(punto)

    if encontrados or info["rayo_optimo"]:
        info["optimos_multiples"] = True
        info["optimos_alternativos"] = encontrados[:5]
        puntos = [actual] + encontrados[:5]
        if info["rayo_optimo"]:
            texto = "El problema tiene infinitas soluciones óptimas (hay una dirección no acotada con el mismo Z)"
        elif len(puntos) == 2:
            texto = f"El problema tiene soluciones óptimas múltiples: Z es el mismo en todo el segmento entre {_punto_texto(puntos[0])} y {_punto_texto(puntos[1])}"
        else:
            texto = "El problema tiene soluciones óptimas múltiples: Z es el mismo entre los vértices " + ", ".join(_punto_texto(p) for p in puntos)
        info["mensajes"].append(texto + ".")
    return info


def alternativos_para_salida(info):
    return [[numero_final(v) for v in punto] for punto in info["optimos_alternativos"]]
