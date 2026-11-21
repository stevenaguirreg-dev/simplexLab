"""Problemas con n variables: validación, resolución con ambos métodos y verificación contra scipy."""
import random
import unittest
from fractions import Fraction

from domain.errores import ProblemaInvalidoError
from domain.validacion import MAX_VARIABLES, validar_problema
from services.servicio_resolucion import ServicioResolucion
from tests.casos import problema

try:
    from scipy.optimize import linprog
except ImportError:  # scipy es solo para pruebas
    linprog = None


def resolver(datos, metodo, modo="paso_a_paso"):
    return ServicioResolucion().resolver({"metodo": metodo, "modo": modo, "problema": datos})


class PruebasValidacionNVariables(unittest.TestCase):
    def mensajes(self, datos):
        with self.assertRaises(ProblemaInvalidoError) as ctx:
            validar_problema(datos)
        return ctx.exception.mensajes

    def test_acepta_cinco_variables(self):
        modelo = validar_problema(problema("max", ["1", "2", "3", "4", "5"], [(["1", "1", "1", "1", "1"], "<=", "10")]))
        self.assertEqual(modelo.num_variables, 5)
        self.assertEqual(modelo.nombres, ["x1", "x2", "x3", "x4", "x5"])
        self.assertFalse(modelo.puede_graficar)

    def test_columnas_finales_vacias_se_ignoran(self):
        modelo = validar_problema(problema("max", ["1", "2", "", "", ""], [(["1", "1", "", "", ""], "<=", "10")]))
        self.assertEqual(modelo.num_variables, 2)

    def test_columna_intermedia_vacia_es_error(self):
        # x3 vacía pero x4 con datos: x3 no puede quedar sin completar.
        m = self.mensajes(problema("max", ["1", "2", "", "4"], [(["1", "1", "", "1"], "<=", "10")]))
        self.assertTrue(any("x3" in x and "vacío" in x for x in m))

    def test_variable_usada_solo_en_una_restriccion(self):
        m = self.mensajes(problema("max", ["1", "2", "3", ""], [(["1", "1", "1", "5"], "<=", "10")]))
        self.assertTrue(any("x4" in x for x in m))

    def test_restriccion_mas_corta_deja_celdas_vacias_y_es_error(self):
        # La restricción 1 no trae x3 pero x3 se usa en la función objetivo: esa celda cuenta como vacía.
        m = self.mensajes(problema("max", ["1", "2", "3"], [(["1", "1"], "<=", "10"), (["1", "1", "1"], "<=", "5")]))
        self.assertTrue(any("Restricción 1" in x and "x3" in x and "vacío" in x for x in m))

    def test_rechaza_mas_variables_que_el_maximo(self):
        n = MAX_VARIABLES + 1
        m = self.mensajes(problema("max", ["1"] * n, [(["1"] * n, "<=", "10")]))
        self.assertTrue(any("máximo" in x for x in m))

    def test_acepta_el_maximo_de_variables(self):
        n = MAX_VARIABLES
        self.assertEqual(validar_problema(problema("max", ["1"] * n, [(["1"] * n, "<=", "10")])).num_variables, n)

    def test_menos_de_dos_variables(self):
        m = self.mensajes(problema("max", ["1"], [(["1"], "<=", "10")]))
        self.assertTrue(any("al menos" in x for x in m))


class PruebasResolucionNVariables(unittest.TestCase):
    def test_problema_de_cuatro_variables_conocido(self):
        # Max 3x1 + 2x2 + 4x3 + x4  s.a.  x1+x2+x3+x4 <= 10 ; x3 <= 4 ; x2 <= 3
        # A mano: x3 = 4 (el mayor coeficiente) y el resto de la capacidad (6) va a x1 -> Z* = 4*4 + 6*3 = 34.
        datos = problema("max", ["3", "2", "4", "1"], [
            (["1", "1", "1", "1"], "<=", "10"),
            (["0", "0", "1", "0"], "<=", "4"),
            (["0", "1", "0", "0"], "<=", "3"),
        ])
        for metodo in ("gran_m", "revisado"):
            r = resolver(datos, metodo)
            self.assertEqual(r["estado"], "optimo", metodo)
            self.assertEqual(r["modelo"]["num_variables"], 4)
            self.assertFalse(r["modelo"]["puede_graficar"])
            self.assertFalse(r["grafico"]["aplica"])
            self.assertEqual(Fraction(r["solucion"]["z"]["fraccion"]), 34, metodo)

    def test_ambos_metodos_dan_los_mismos_tableros(self):
        datos = problema("max", ["3", "2", "4", "1", "5"], [
            (["1", "2", "1", "1", "1"], "<=", "40"),
            (["2", "0", "3", "1", "2"], "<=", "50"),
            (["1", "4", "0", "2", "1"], "<=", "60"),
        ])
        a, b = resolver(datos, "gran_m"), resolver(datos, "revisado")
        self.assertEqual(a["solucion"]["z"], b["solucion"]["z"])
        for pa, pb in zip(a["pasos"], b["pasos"]):
            self.assertEqual(pa["instantanea"]["fila_z"], pb["instantanea"]["fila_z"])
            self.assertEqual(
                [f["valores"] for f in pa["instantanea"]["filas"]],
                [f["valores"] for f in pb["instantanea"]["filas"]],
            )

    def test_sensibilidad_y_resumen_con_seis_variables(self):
        datos = problema("max", ["3", "2", "4", "1", "5", "2"], [
            (["1", "2", "1", "1", "1", "1"], "<=", "40"),
            (["2", "0", "3", "1", "2", "1"], "<=", "50"),
            (["1", "4", "0", "2", "1", "3"], "<=", "60"),
        ])
        r = resolver(datos, "revisado")
        self.assertEqual(r["estado"], "optimo")
        self.assertEqual(len(r["solucion"]["variables"]), 6)
        self.assertEqual(len(r["sensibilidad"]["rangos_coeficientes"]), 6)

    def test_infactible_y_no_acotado_con_n_variables(self):
        infact = problema("max", ["1", "1", "1", "1"], [(["1", "1", "1", "1"], "<=", "2"), (["1", "1", "1", "1"], ">=", "5")])
        noacot = problema("max", ["1", "1", "1", "1"], [(["1", "-1", "0", "0"], "<=", "1"), (["0", "0", "1", "-1"], "<=", "2")])
        for metodo in ("gran_m", "revisado"):
            self.assertEqual(resolver(infact, metodo)["estado"], "infactible", metodo)
            self.assertEqual(resolver(noacot, metodo)["estado"], "no_acotado", metodo)


def problema_aleatorio(rng, n, m):
    """Problema factible y acotado con mezcla de <=, >= y =. Se construye a partir de un punto factible x0."""
    x0 = [rng.randint(0, 6) for _ in range(n)]
    restricciones = []
    for _ in range(m):
        coef = [rng.randint(-3, 6) for _ in range(n)]
        valor = sum(a * x for a, x in zip(coef, x0))
        rel = rng.choice(["<=", "<=", ">=", "="])
        holgura = rng.randint(0, 8)
        rhs = valor + holgura if rel == "<=" else valor - holgura if rel == ">=" else valor
        restricciones.append((coef, rel, rhs))
    # Una restricción que acota el problema.
    restricciones.append(([1] * n, "<=", sum(x0) + rng.randint(1, 10)))
    sentido = rng.choice(["max", "min"])
    c = [rng.randint(-5, 9) for _ in range(n)]
    return sentido, c, restricciones


@unittest.skipIf(linprog is None, "scipy no está instalado")
class PruebasContraScipy(unittest.TestCase):
    def comprobar(self, semilla, n, m):
        rng = random.Random(semilla)
        sentido, c, restricciones = problema_aleatorio(rng, n, m)
        datos = problema(sentido, [str(v) for v in c], [([str(a) for a in coef], rel, str(rhs)) for coef, rel, rhs in restricciones])

        A_ub, b_ub, A_eq, b_eq = [], [], [], []
        for coef, rel, rhs in restricciones:
            if rel == "<=":
                A_ub.append(coef); b_ub.append(rhs)
            elif rel == ">=":
                A_ub.append([-a for a in coef]); b_ub.append(-rhs)
            else:
                A_eq.append(coef); b_eq.append(rhs)
        objetivo = c if sentido == "min" else [-v for v in c]
        esperado = linprog(objetivo, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None,
                           bounds=[(0, None)] * n, method="highs")
        self.assertEqual(esperado.status, 0, f"semilla {semilla}: scipy no encontró óptimo")
        z_esperado = esperado.fun if sentido == "min" else -esperado.fun

        for metodo in ("gran_m", "revisado"):
            r = resolver(datos, metodo, modo="inmediata")
            self.assertEqual(r["estado"], "optimo", f"semilla {semilla} n={n} {metodo}")
            z = float(Fraction(r["solucion"]["z"]["fraccion"]))
            self.assertAlmostEqual(z, z_esperado, places=6, msg=f"semilla {semilla} n={n} m={m} {metodo}")
            # La solución devuelta debe cumplir todas las restricciones.
            x = [Fraction(v["valor"]["fraccion"]) for v in r["solucion"]["variables"]]
            self.assertTrue(all(v >= 0 for v in x))
            for coef, rel, rhs in restricciones:
                lhs = sum(Fraction(a) * v for a, v in zip(coef, x))
                self.assertTrue(
                    (rel == "<=" and lhs <= rhs) or (rel == ">=" and lhs >= rhs) or (rel == "=" and lhs == rhs),
                    f"semilla {semilla} {metodo}: restricción violada",
                )

    def test_problemas_aleatorios_de_2_a_12_variables(self):
        semilla = 0
        for n in range(2, 13):
            for m in (2, 4, 7):
                for _ in range(4):
                    semilla += 1
                    self.comprobar(semilla, n, m)


if __name__ == "__main__":
    unittest.main()
