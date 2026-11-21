"""Validación de la entrada del usuario y construcción del modelo.

El número de variables n lo define la función objetivo (mínimo 2, máximo MAX_VARIABLES).
Regla de las columnas finales: si las últimas variables (x3, x4, ...) están vacías en la
función objetivo y en todas las restricciones, se ignoran. Si una variable tiene datos en
algún lugar, todas sus celdas deben estar completas (use 0 donde no participe).
"""
import math
from fractions import Fraction

from .errores import ProblemaInvalidoError
from .modelos import Restriccion, crear_modelo

RELACIONES = {"<=": "<=", "≤": "<=", ">=": ">=", "≥": ">=", "=": "=", "==": "="}
MIN_VARIABLES = 2
MAX_VARIABLES = 30
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
    if not isinstance(fo, list) or len(fo) < MIN_VARIABLES:
        errores.append(f"La función objetivo debe tener los coeficientes de al menos {MIN_VARIABLES} variables (x1, x2, ...).")
        fo = None
    elif len(fo) > MAX_VARIABLES:
        errores.append(f"Se permiten máximo {MAX_VARIABLES} variables.")
        fo = None
    if not isinstance(restr, list) or len(restr) == 0:
        errores.append("Agregue al menos una restricción.")
        restr = None
    elif len(restr) > MAX_RESTRICCIONES:
        errores.append(f"Se permiten máximo {MAX_RESTRICCIONES} restricciones.")
        restr = None
    if fo is None or restr is None:
        raise ProblemaInvalidoError(errores)

    filas = []
    for i, r in enumerate(restr, start=1):
        if not isinstance(r, dict):
            errores.append(f"Restricción {i}: formato inválido.")
            continue
        coef = r.get("coeficientes")
        if not isinstance(coef, list) or not (MIN_VARIABLES <= len(coef) <= MAX_VARIABLES):
            errores.append(f"Restricción {i}: debe tener los coeficientes de las variables x1, x2, ... (entre {MIN_VARIABLES} y {MAX_VARIABLES}).")
            continue
        rel = RELACIONES.get(str(r.get("relacion", "")).strip())
        if rel is None:
            errores.append(f"Restricción {i}: el tipo debe ser ≤, ≥ o =.")
        filas.append((i, list(coef), rel, r.get("rhs")))
    if errores:
        raise ProblemaInvalidoError(errores)

    # Todas las listas se igualan al ancho mayor; lo que falte cuenta como celda vacía.
    ancho = max([len(fo)] + [len(coef) for _, coef, _, _ in filas])
    fo = list(fo) + [None] * (ancho - len(fo))
    filas = [(i, coef + [None] * (ancho - len(coef)), rel, rhs) for i, coef, rel, rhs in filas]

    def columna_vacia(j):
        return _convertir(fo[j]) is VACIO and all(_convertir(coef[j]) is VACIO for _, coef, _, _ in filas)

    n = ancho
    while n > MIN_VARIABLES and columna_vacia(n - 1):
        n -= 1

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
        if n > MIN_VARIABLES:
            errores.append(f"Nota: el problema usa {n} variables (hasta x{n}), así que todas sus celdas deben completarse (use 0 si no participa).")
        raise ProblemaInvalidoError(errores)

    return crear_modelo(
        sentido,
        c,
        [Restriccion(coef, rel, lado) for coef, rel, lado in restricciones],
    )
