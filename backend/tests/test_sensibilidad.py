"""Sensibilidad: valores de clase (Wyndor) y coherencia por re-resolución."""
import copy
import unittest
from fractions import Fraction

from tests.casos import CLASE, ENUNCIADO
from tests.test_casos_enunciado import resolver


def f(numero):
    return None if numero is None else Fraction(numero["fraccion"])


class PruebasSensibilidad(unittest.TestCase):
    def test_wyndor_coincide_con_la_clase_12(self):
        for metodo in ("gran_m", "revisado"):
            s = resolver(CLASE["wyndor"], metodo)["sensibilidad"]
            self.assertEqual([f(p["valor"]) for p in s["precios_sombra"]], [0, Fraction(3, 2), 1])
            rc = {r["variable"]: (f(r["minimo"]), f(r["maximo"])) for r in s["rangos_coeficientes"]}
            self.assertEqual(rc["x1"], (0, Fraction(15, 2)))
            self.assertEqual(rc["x2"], (2, None))
            rb = [(f(r["minimo"]), f(r["maximo"])) for r in s["rangos_lado_derecho"]]
            self.assertEqual(rb, [(2, None), (6, 18), (12, 24)])

    def test_segundo_ejemplo_de_clase(self):
        s = resolver(CLASE["sensibilidad"], "revisado")["sensibilidad"]
        self.assertEqual(f(s["precios_sombra"][0]["valor"]), 1)
        self.assertEqual(f(s["precios_sombra"][1]["valor"]), 3)

    def variar_rhs(self, problema, i, nuevo):
        p = copy.deepcopy(problema)
        p["restricciones"][i]["rhs"] = str(nuevo)
        return resolver(p, "gran_m", "inmediata")

    def variar_c(self, problema, j, nuevo):
        p = copy.deepcopy(problema)
        p["funcion_objetivo"][j] = str(nuevo)
        return resolver(p, "gran_m", "inmediata")

    def test_precio_sombra_y_rango_rhs_se_cumplen_al_re_resolver(self):
        casos = [CLASE["wyndor"], CLASE["sensibilidad"], ENUNCIADO[1], ENUNCIADO[2], ENUNCIADO[3], CLASE["dieta"], CLASE["camion"]]
        for problema in casos:
            base = resolver(problema, "gran_m")
            z0 = f(base["solucion"]["z"])
            for i, (p, rg) in enumerate(zip(base["sensibilidad"]["precios_sombra"], base["sensibilidad"]["rangos_lado_derecho"])):
                b0 = f(rg["actual"])
                pi = f(p["valor"])
                for extremo in (f(rg["minimo"]), f(rg["maximo"])):
                    if extremo is None:
                        continue
                    r = self.variar_rhs(problema, i, extremo)
                    self.assertEqual(r["estado"], "optimo")
                    self.assertEqual(f(r["solucion"]["z"]), z0 + pi * (extremo - b0), f"rhs R{i + 1}")

    def test_rango_de_costos_conserva_la_solucion(self):
        casos = [CLASE["wyndor"], CLASE["sensibilidad"], ENUNCIADO[1], ENUNCIADO[3], CLASE["dieta"], CLASE["camion"]]
        for problema in casos:
            base = resolver(problema, "gran_m")
            x0 = {v["nombre"]: f(v["valor"]) for v in base["solucion"]["variables"]}
            z0 = f(base["solucion"]["z"])
            for j, rg in enumerate(base["sensibilidad"]["rangos_coeficientes"]):
                c0 = f(rg["actual"])
                for extremo in (f(rg["minimo"]), f(rg["maximo"])):
                    if extremo is None:
                        continue
                    r = self.variar_c(problema, j, extremo)
                    esperado = z0 + (extremo - c0) * x0[rg["variable"]]
                    self.assertEqual(f(r["solucion"]["z"]), esperado, f"c{j + 1} en {extremo}")


class PruebasContraScipy(unittest.TestCase):
    """Verificación cruzada. scipy solo se usa aquí, nunca para producir resultados."""

    def test_estado_y_z_coinciden_en_problemas_aleatorios(self):
        try:
            import random
            from scipy.optimize import linprog
        except ImportError:
            self.skipTest("scipy no está instalado")
        rnd = random.Random(7)
        comprobados = 0
        for _ in range(150):
            n = rnd.choice([2, 3])
            sentido = rnd.choice(["max", "min"])
            c = [rnd.randint(-6, 9) for _ in range(n)]
            filas = []
            for _ in range(rnd.randint(1, 4)):
                coef = [rnd.randint(-4, 6) for _ in range(n)]
                filas.append((coef, rnd.choice(["<=", ">=", "="]), rnd.randint(-8, 30)))
            problema = {
                "sentido": sentido,
                "funcion_objetivo": [str(v) for v in c] + ([""] if n == 2 else []),
                "restricciones": [
                    {"coeficientes": [str(v) for v in coef] + ([""] if n == 2 else []), "relacion": rel, "rhs": str(b)}
                    for coef, rel, b in filas
                ],
            }
            A_ub, b_ub, A_eq, b_eq = [], [], [], []
            for coef, rel, b in filas:
                if rel == "<=":
                    A_ub.append(coef); b_ub.append(b)
                elif rel == ">=":
                    A_ub.append([-v for v in coef]); b_ub.append(-b)
                else:
                    A_eq.append(coef); b_eq.append(b)
            costo = c if sentido == "min" else [-v for v in c]
            ref = linprog(costo, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=[(0, None)] * n, method="highs")
            if ref.status not in (0, 2, 3):
                continue
            for metodo in ("gran_m", "revisado"):
                mio = resolver(problema, metodo)
                esperado = {0: "optimo", 2: "infactible", 3: "no_acotado"}[ref.status]
                self.assertEqual(mio["estado"], esperado, (problema, metodo))
                if ref.status == 0:
                    z = float(f(mio["solucion"]["z"]))
                    z_ref = ref.fun if sentido == "min" else -ref.fun
                    self.assertAlmostEqual(z, z_ref, places=6, msg=str(problema))
                    # el precio sombra debe coincidir con el dual de HiGHS cuando no hay degeneración
            comprobados += 1
        self.assertGreater(comprobados, 100)


if __name__ == "__main__":
    unittest.main()
