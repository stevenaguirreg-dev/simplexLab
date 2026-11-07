"""Validación de la entrada del usuario y construcción del modelo.

Regla de x3: si x3 está vacía en la función objetivo y en todas las
restricciones, el problema se interpreta con 2 variables. Si x3 aparece en
algún lugar, todas sus celdas deben estar completas (use 0 donde no participe).
"""
import math
from fractions import Fraction

from .errores import ProblemaInvalidoError
from .modelos import Restriccion, crear_modelo

RELACIONES = {"<=": "<=", "≤": "<=", ">=": ">=", "≥": ">=", "=": "=", "==": "="}
MAX_RESTRICCIONES = 100
VACIO = object()


def _convertir(valor):
    """Devuelve Fraction, VACIO, o None si no es un número válido."""
    if valor is None:
        return VACIO
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and not math.isfinite(valor):
            return None
        return Fraction(str(valor))
    if isinstance(valor, str):
        texto = valor.strip().replace(",", ".")
        if texto == "":
            return VACIO
        try:
            return Fraction(texto)
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _celda(valor, descripcion, errores):
    """Convierte una celda; registra el error y devuelve None si es inválida."""
    numero = _convertir(valor)
    if numero is VACIO:
        errores.append(f"{descripcion}: está vacío.")
        return None
    if numero is None:
        errores.append(f"{descripcion}: '{valor}' no es un número válido (use enteros, decimales o fracciones como 1/3).")
        return None
    return numero


def validar_problema(datos):
    """Valida el diccionario del problema y devuelve el ModeloPL correspondiente."""
    errores = []
    if not isinstance(datos, dict):
        raise ProblemaInvalidoError(["El problema debe enviarse como un objeto con sentido, función objetivo y restricciones."])

    sentido = str(datos.get("sentido", "")).strip().lower()
    if sentido not in ("max", "min"):
        errores.append("El sentido de la función objetivo debe ser Max o Min.")

    fo = datos.get("funcion_objetivo")
    restr = datos.get("restricciones")
    if not isinstance(fo, list) or len(fo) not in (2, 3):
        errores.append("La función objetivo debe tener los coeficientes de x1, x2 y x3.")
        fo = None
    if not isinstance(restr, list) or len(restr) == 0:
        errores.append("Agregue al menos una restricción.")
        restr = None
    elif len(restr) > MAX_RESTRICCIONES:
        errores.append(f"Se permiten máximo {MAX_RESTRICCIONES} restricciones.")
        restr = None
    if fo is None or restr is None:
        raise ProblemaInvalidoError(errores)

    ancho = 3
    fo = list(fo) + [None] * (ancho - len(fo))
    filas = []
    for i, r in enumerate(restr, start=1):
        if not isinstance(r, dict):
            errores.append(f"Restricción {i}: formato inválido.")
            continue
        coef = r.get("coeficientes")
        if not isinstance(coef, list) or len(coef) not in (2, 3):
            errores.append(f"Restricción {i}: debe tener los coeficientes de x1, x2 y x3.")
            continue
        coef = list(coef) + [None] * (ancho - len(coef))
        rel = RELACIONES.get(str(r.get("relacion", "")).strip())
        if rel is None:
            errores.append(f"Restricción {i}: el tipo debe ser ≤, ≥ o =.")
        filas.append((i, coef, rel, r.get("rhs")))
    if errores:
        raise ProblemaInvalidoError(errores)

    x3_presente = _convertir(fo[2]) is not VACIO or any(_convertir(c[2]) is not VACIO for _, c, _, _ in filas)
    n = 3 if x3_presente else 2

    c = []
    for j in range(n):
        valor = _celda(fo[j], f"Función objetivo, coeficiente de x{j + 1}", errores)
        c.append(valor)

    restricciones = []
    for i, coef, rel, rhs in filas:
        coeficientes = [_celda(coef[j], f"Restricción {i}, coeficiente de x{j + 1}", errores) for j in range(n)]
        lado = _celda(rhs, f"Restricción {i}, lado derecho", errores)
        restricciones.append((coeficientes, rel, lado))

    if errores:
        if x3_presente:
            errores.append("Nota: x3 tiene datos, así que todas sus celdas deben completarse (use 0 si no participa).")
        raise ProblemaInvalidoError(errores)

    return crear_modelo(
        n,
        sentido,
        c,
        [Restriccion(coef, rel, lado) for coef, rel, lado in restricciones],
    )
