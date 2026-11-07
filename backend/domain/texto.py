"""Utilidades para escribir expresiones lineales legibles (x1 + 2x2 - x3)."""
from fractions import Fraction


def _coeficiente(magnitud):
    if magnitud == 1:
        return ""
    if magnitud.denominator == 1:
        return str(magnitud)
    return f"({magnitud})"


def expresion_lineal(coeficientes, nombres):
    """Devuelve por ejemplo '2x1 - x2 + 3/2x3'. Si todo es cero devuelve '0'."""
    partes = []
    for c, nombre in zip(coeficientes, nombres):
        c = Fraction(c)
        if c == 0:
            continue
        signo = "-" if c < 0 else "+"
        termino = f"{_coeficiente(abs(c))}{nombre}"
        if not partes:
            partes.append(termino if signo == "+" else f"-{termino}")
        else:
            partes.append(f"{signo} {termino}")
    return " ".join(partes) if partes else "0"


SIMBOLOS = {"<=": "≤", ">=": "≥", "=": "="}
