"""Aritmética exacta: fracciones y el número a + b·M del método de la Gran M.

Todo el cálculo se hace con fracciones. Solo al entregar resultados se muestra
también el decimal (con 4 cifras).
"""
from fractions import Fraction
from functools import total_ordering

DECIMALES = 4


def _texto_fraccion(f):
    return str(Fraction(f))


@total_ordering
class GranM:
    """Número de la forma a + b·M, con M un valor positivo arbitrariamente grande.

    Se compara primero por el coeficiente de M y luego por la parte constante,
    que es exactamente lo que significa "M muy grande".
    """

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a = Fraction(a)
        self.b = Fraction(b)

    @staticmethod
    def _convertir(otro):
        if isinstance(otro, GranM):
            return otro
        if isinstance(otro, (int, Fraction)):
            return GranM(otro, 0)
        return None

    def __add__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        return GranM(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __sub__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        return GranM(self.a - o.a, self.b - o.b)

    def __rsub__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        return GranM(o.a - self.a, o.b - self.b)

    def __neg__(self):
        return GranM(-self.a, -self.b)

    def __mul__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        if self.b != 0 and o.b != 0:
            raise ArithmeticError("El producto M·M no se usa en este método.")
        return GranM(self.a * o.a, self.a * o.b + self.b * o.a)

    __rmul__ = __mul__

    def __truediv__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        if o.b != 0:
            raise ArithmeticError("No se divide por un número que contiene M.")
        return GranM(self.a / o.a, self.b / o.a)

    def _clave(self):
        return (self.b, self.a)

    def __eq__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        return self._clave() == o._clave()

    def __lt__(self, otro):
        o = self._convertir(otro)
        if o is None:
            return NotImplemented
        return self._clave() < o._clave()

    def __hash__(self):
        return hash(self._clave())

    def tiene_m(self):
        return self.b != 0

    def __str__(self):
        a, b = self.a, self.b
        if b == 0:
            return _texto_fraccion(a)
        if b == 1:
            parte_m = "M"
        elif b == -1:
            parte_m = "-M"
        elif b.denominator == 1:
            parte_m = f"{b}M"
        else:
            parte_m = f"({b})M"
        if a == 0:
            return parte_m
        signo = "+" if a > 0 else "-"
        return f"{parte_m} {signo} {_texto_fraccion(abs(a))}"

    __repr__ = __str__


def numero_final(valor):
    """Resultado para el usuario: fracción exacta + decimal con 4 cifras."""
    f = Fraction(valor)
    decimal = round(float(f), DECIMALES)
    exacto = Fraction(str(decimal)) == f
    return {"fraccion": _texto_fraccion(f), "decimal": decimal, "exacto": exacto}


def numero_final_o_nulo(valor):
    return None if valor is None else numero_final(valor)
