"""Método gráfico para dos variables, con geometría exacta (fracciones).

Calcula: región factible (recortada a una caja de dibujo), vértices con su Z,
rectas de las restricciones y la recta de la función objetivo en el óptimo.
Funciona igual con regiones acotadas, no acotadas o vacías.
"""
from fractions import Fraction
from itertools import combinations

from .numeros import numero_final
from .texto import SIMBOLOS, expresion_lineal

COLOR_MARGEN = Fraction(6, 5)


def _evaluar(semiplano, p):
    a1, a2, b = semiplano
    return a1 * p[0] + a2 * p[1] - b


def _recortar(poligono, semiplano):
    """Sutherland-Hodgman: conserva la parte del polígono donde a1x + a2y <= b."""
    if not poligono:
        return []
    salida = []
    for i, actual in enumerate(poligono):
        previo = poligono[i - 1]
        v_act, v_prev = _evaluar(semiplano, actual), _evaluar(semiplano, previo)
        if v_act <= 0:
            if v_prev > 0:
                salida.append(_interseccion(previo, actual, v_prev, v_act))
            salida.append(actual)
        elif v_prev <= 0:
            salida.append(_interseccion(previo, actual, v_prev, v_act))
    limpio = []
    for p in salida:
        if not limpio or p != limpio[-1]:
            limpio.append(p)
    if len(limpio) > 1 and limpio[0] == limpio[-1]:
        limpio.pop()
    return limpio


def _interseccion(p, q, vp, vq):
    t = vp / (vp - vq)
    return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))


def _segmento_en_caja(a1, a2, b, X, Y):
    """Tramo de la recta a1x + a2y = b que cae dentro de [0,X] x [0,Y]."""
    puntos = []
    if a2 != 0:
        for x in (Fraction(0), X):
            y = (b - a1 * x) / a2
            if 0 <= y <= Y:
                puntos.append((x, y))
    if a1 != 0:
        for y in (Fraction(0), Y):
            x = (b - a2 * y) / a1
            if 0 <= x <= X:
                puntos.append((x, y))
    unicos = sorted(set(puntos))
    if len(unicos) < 2:
        return None
    return [unicos[0], unicos[-1]]


def _flt(p):
    return [float(p[0]), float(p[1])]


class AnalizadorGrafico:
    def __init__(self, modelo):
        self.modelo = modelo

    def _semiplanos(self):
        planos = []
        for r in self.modelo.restricciones:
            a1, a2 = r.coeficientes
            if r.relacion in ("<=", "="):
                planos.append((a1, a2, r.rhs))
            if r.relacion in (">=", "="):
                planos.append((-a1, -a2, -r.rhs))
        planos += [(Fraction(-1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(-1), Fraction(0))]
        return planos

    def _es_factible(self, p):
        return all(_evaluar(s, p) <= 0 for s in self._semiplanos())

    def _vertices(self):
        rectas = []
        for r in self.modelo.restricciones:
            a1, a2 = r.coeficientes
            if a1 != 0 or a2 != 0:
                rectas.append((a1, a2, r.rhs))
        rectas += [(Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0))]
        puntos = set()
        for (a1, a2, b), (c1, c2, d) in combinations(rectas, 2):
            det = a1 * c2 - a2 * c1
            if det == 0:
                continue
            puntos.add(((b * c2 - a2 * d) / det, (a1 * d - b * c1) / det))
        return sorted(puntos)

    def _intersectos(self):
        """Cortes positivos de las rectas con los ejes (ayudan a elegir la escala)."""
        xs, ys = [], []
        for r in self.modelo.restricciones:
            a1, a2 = r.coeficientes
            if a1 != 0 and r.rhs / a1 > 0:
                xs.append(r.rhs / a1)
            if a2 != 0 and r.rhs / a2 > 0:
                ys.append(r.rhs / a2)
        return xs, ys

    def calcular(self, contexto):
        """contexto: {'estado', 'z' (Fraction|None), 'optimos' (lista de puntos Fraction)}."""
        m = self.modelo
        c1, c2 = m.c
        vertices = self._vertices()
        factibles = [p for p in vertices if self._es_factible(p)]
        cortes_x, cortes_y = self._intersectos()

        base_x = [p[0] for p in factibles] + cortes_x
        base_y = [p[1] for p in factibles] + cortes_y
        escala = max(base_x + base_y + [Fraction(1)])
        grande = escala * 1000
        caja_enorme = [(Fraction(0), Fraction(0)), (grande, Fraction(0)), (grande, grande), (Fraction(0), grande)]
        region = caja_enorme
        for s in self._semiplanos():
            region = _recortar(region, s)
        vacia = len(region) == 0
        no_acotada = (not vacia) and any(p[0] == grande or p[1] == grande for p in region)

        if no_acotada:
            # región abierta: se deja el doble de espacio para que se note que continúa
            max_x = max(base_x + [Fraction(0)]) * Fraction(5, 3)
            max_y = max(base_y + [Fraction(0)]) * Fraction(5, 3)
        else:
            fx = max([p[0] for p in factibles] + [Fraction(0)])
            fy = max([p[1] for p in factibles] + [Fraction(0)])
            # se amplía el recuadro (hasta 2x la región) para que también se vean las restricciones redundantes
            max_x = max(fx, min(max(cortes_x + [Fraction(0)]), 2 * fx))
            max_y = max(fy, min(max(cortes_y + [Fraction(0)]), 2 * fy))
            if not factibles:
                max_x, max_y = max(cortes_x + [Fraction(10)]), max(cortes_y + [Fraction(10)])
        X = max_x * COLOR_MARGEN if max_x > 0 else (max_y * COLOR_MARGEN if max_y > 0 else Fraction(10))
        Y = max_y * COLOR_MARGEN if max_y > 0 else (max_x * COLOR_MARGEN if max_x > 0 else Fraction(10))

        caja = [(Fraction(0), Fraction(0)), (X, Fraction(0)), (X, Y), (Fraction(0), Y)]
        poligono = caja
        for s in self._semiplanos():
            poligono = _recortar(poligono, s)

        restricciones = []
        for i, r in enumerate(m.restricciones, start=1):
            a1, a2 = r.coeficientes
            segmento = _segmento_en_caja(a1, a2, r.rhs, X, Y) if (a1 != 0 or a2 != 0) else None
            restricciones.append({
                "numero": i,
                "etiqueta": f"R{i}",
                "expresion": f"{expresion_lineal(r.coeficientes, m.nombres)} {SIMBOLOS[r.relacion]} {r.rhs}",
                "segmento": None if segmento is None else [_flt(p) for p in segmento],
            })

        z_opt = contexto.get("z")
        optimos = contexto.get("optimos") or []
        lista_vertices = []
        for p in factibles:
            z = c1 * p[0] + c2 * p[1]
            lista_vertices.append({
                "x": numero_final(p[0]), "y": numero_final(p[1]), "z": numero_final(z),
                "factible": True, "es_optimo": z_opt is not None and z == z_opt,
            })
        for p in vertices:
            if p not in factibles and p[0] <= X and p[1] <= Y:
                lista_vertices.append({
                    "x": numero_final(p[0]), "y": numero_final(p[1]), "z": numero_final(c1 * p[0] + c2 * p[1]),
                    "factible": False, "es_optimo": False,
                })

        optimo = None
        if contexto.get("estado") == "optimo" and z_opt is not None:
            recta = None
            if c1 != 0 or c2 != 0:
                tramo = _segmento_en_caja(c1, c2, z_opt, X, Y)
                recta = None if tramo is None else [_flt(p) for p in tramo]
            optimo = {
                "z": numero_final(z_opt),
                "puntos": [{"x": numero_final(p[0]), "y": numero_final(p[1])} for p in optimos],
                "recta": recta,
                "expresion": f"{expresion_lineal([c1, c2], m.nombres)} = {z_opt}",
            }

        if vacia:
            mensaje = "La región factible está vacía: las restricciones no se pueden cumplir a la vez."
        elif no_acotada:
            mensaje = "La región factible no está acotada (se extiende más allá del recuadro dibujado)."
        else:
            mensaje = "Región factible acotada."
        return {
            "aplica": True,
            "mensaje": mensaje,
            "caja": {"x_max": float(X), "y_max": float(Y)},
            "region": {"poligono": [_flt(p) for p in poligono] if not vacia else [], "vacia": vacia, "no_acotada": no_acotada},
            "restricciones": restricciones,
            "vertices": lista_vertices,
            "optimo": optimo,
        }
