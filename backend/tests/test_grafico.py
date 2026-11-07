"""Método gráfico: región, vértices con Z y recta de Z en el óptimo."""
import unittest
from fractions import Fraction

from tests.casos import ENUNCIADO
from tests.test_casos_enunciado import resolver


class PruebasGrafico(unittest.TestCase):
    def test_problema_1_vertices_region_y_recta_optima(self):
        g = resolver(ENUNCIADO[1], "gran_m")["grafico"]
        factibles = {(Fraction(v["x"]["fraccion"]), Fraction(v["y"]["fraccion"])): Fraction(v["z"]["fraccion"]) for v in g["vertices"] if v["factible"]}
        self.assertEqual(factibles, {(0, 0): 0, (0, 30): 2400, (42, 16): 3380, (50, 0): 2500})
        optimos = [v for v in g["vertices"] if v["es_optimo"]]
        self.assertEqual(len(optimos), 1)
        self.assertEqual(len(g["region"]["poligono"]), 4)
        self.assertIsNotNone(g["optimo"]["recta"])
        self.assertFalse(g["region"]["no_acotada"])
        # la restricción redundante x2 <= 40 debe quedar dentro del recuadro para poder verse
        self.assertGreaterEqual(g["caja"]["y_max"], 40)
        self.assertTrue(all(r["segmento"] for r in g["restricciones"]))

    def test_infactible_no_dibuja_region_ni_recta(self):
        g = resolver(ENUNCIADO[4], "revisado")["grafico"]
        self.assertTrue(g["region"]["vacia"])
        self.assertEqual(g["region"]["poligono"], [])
        self.assertIsNone(g["optimo"])

    def test_no_acotado_marca_region_abierta_sin_recta(self):
        g = resolver(ENUNCIADO[5], "revisado")["grafico"]
        self.assertTrue(g["region"]["no_acotada"])
        self.assertIsNone(g["optimo"])

    def test_optimos_multiples_marca_los_dos_vertices(self):
        g = resolver(ENUNCIADO[6], "gran_m")["grafico"]
        self.assertEqual(len([v for v in g["vertices"] if v["es_optimo"]]), 2)

    def test_tres_variables_indica_que_no_aplica(self):
        g = resolver(ENUNCIADO[3], "gran_m")["grafico"]
        self.assertFalse(g["aplica"])
        self.assertIn("no aplica", g["mensaje"])


if __name__ == "__main__":
    unittest.main()
