"""Los 7 problemas del enunciado, con ambos métodos."""
import unittest
from fractions import Fraction

from services.servicio_resolucion import ServicioResolucion
from tests.casos import ENUNCIADO

METODOS = ("gran_m", "revisado")


def resolver(problema, metodo, modo="paso_a_paso"):
    return ServicioResolucion().resolver({"metodo": metodo, "modo": modo, "problema": problema})


def valores(r):
    return {v["nombre"]: Fraction(v["valor"]["fraccion"]) for v in r["solucion"]["variables"]}


class PruebasEnunciado(unittest.TestCase):
    def para_ambos(self, numero):
        for metodo in METODOS:
            with self.subTest(metodo=metodo):
                yield resolver(ENUNCIADO[numero], metodo)

    def test_1_redundante_y_grafico(self):
        for r in self.para_ambos(1):
            self.assertEqual(r["estado"], "optimo")
            self.assertEqual(valores(r), {"x1": 42, "x2": 16})
            self.assertEqual(r["solucion"]["z"]["fraccion"], "3380")
            self.assertTrue(r["grafico"]["aplica"])
            # la restricción x2 <= 40 es redundante: queda con holgura 24
            self.assertEqual(r["solucion"]["restricciones"][2]["valor"]["fraccion"], "24")

    def test_2_minimizacion_con_artificiales(self):
        for r in self.para_ambos(2):
            self.assertEqual(valores(r), {"x1": Fraction(2, 5), "x2": Fraction(9, 5)})
            self.assertEqual(r["solucion"]["z"]["fraccion"], "17/5")
            self.assertEqual(r["solucion"]["z"]["decimal"], 3.4)

    def test_3_tres_variables_sin_grafico(self):
        for r in self.para_ambos(3):
            self.assertEqual(valores(r), {"x1": 0, "x2": 100, "x3": 230})
            self.assertEqual(r["solucion"]["z"]["fraccion"], "1350")
            self.assertFalse(r["grafico"]["aplica"])

    def test_4_infactible(self):
        for r in self.para_ambos(4):
            self.assertEqual(r["estado"], "infactible")
            self.assertIn("no tiene solución factible", r["mensaje"])
            self.assertTrue(r["grafico"]["region"]["vacia"])

    def test_5_no_acotado(self):
        for r in self.para_ambos(5):
            self.assertEqual(r["estado"], "no_acotado")
            self.assertIn("no acotada", r["mensaje"])
            self.assertTrue(r["grafico"]["region"]["no_acotada"])

    def test_6_optimos_multiples(self):
        for r in self.para_ambos(6):
            self.assertEqual(r["solucion"]["z"]["fraccion"], "10")
            self.assertTrue(r["casos_especiales"]["optimos_multiples"])
            puntos = [tuple(Fraction(v["valor"]["fraccion"]) for v in r["solucion"]["variables"])]
            puntos += [tuple(Fraction(v["fraccion"]) for v in p) for p in r["solucion"]["optimos_alternativos"]]
            self.assertEqual(set(puntos), {(Fraction(0), Fraction(5, 2)), (Fraction(3), Fraction(1))})

    def test_7_degeneracion(self):
        for r in self.para_ambos(7):
            self.assertEqual(valores(r), {"x1": 0, "x2": 2})
            self.assertEqual(r["solucion"]["z"]["fraccion"], "18")
            self.assertTrue(r["casos_especiales"]["degenerado"])
            self.assertTrue(r["casos_especiales"]["variables_basicas_en_cero"])

    def test_ambos_metodos_recorren_las_mismas_bases(self):
        for numero, problema in ENUNCIADO.items():
            with self.subTest(problema=numero):
                r = resolver(problema, "gran_m")
                self.assertTrue(r["comparacion"]["misma_secuencia_de_bases"])
                self.assertTrue(r["comparacion"]["mismo_estado"])


if __name__ == "__main__":
    unittest.main()
