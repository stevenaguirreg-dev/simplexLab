"""Validación de entrada: mensajes claros y regla de x3."""
import unittest

from domain.errores import ProblemaInvalidoError
from domain.validacion import validar_problema
from tests.casos import ENUNCIADO, problema


class PruebasValidacion(unittest.TestCase):
    def mensajes(self, datos):
        with self.assertRaises(ProblemaInvalidoError) as ctx:
            validar_problema(datos)
        return ctx.exception.mensajes

    def test_x3_vacia_en_todo_el_problema_es_modelo_de_dos_variables(self):
        self.assertEqual(validar_problema(ENUNCIADO[1]).num_variables, 2)

    def test_x3_con_datos_es_modelo_de_tres_variables(self):
        self.assertEqual(validar_problema(ENUNCIADO[3]).num_variables, 3)

    def test_acepta_fracciones_y_decimales(self):
        modelo = validar_problema(problema("max", ["1/3", "0.5", ""], [(["1", "2", ""], "<=", "3/2")]))
        self.assertEqual(str(modelo.c[0]), "1/3")
        self.assertEqual(str(modelo.c[1]), "1/2")

    def test_campo_vacio(self):
        m = self.mensajes(problema("max", ["", "2", ""], [(["1", "2", ""], "<=", "5")]))
        self.assertTrue(any("x1" in x and "vacío" in x for x in m))

    def test_valor_no_numerico(self):
        m = self.mensajes(problema("max", ["1", "2", ""], [(["abc", "2", ""], "<=", "5")]))
        self.assertTrue(any("abc" in x for x in m))

    def test_lado_derecho_vacio(self):
        m = self.mensajes(problema("max", ["1", "2", ""], [(["1", "2", ""], "<=", "")]))
        self.assertTrue(any("lado derecho" in x for x in m))

    def test_x3_usada_pero_incompleta(self):
        m = self.mensajes(problema("max", ["1", "2", "3"], [(["1", "2", ""], "<=", "5")]))
        self.assertTrue(any("x3" in x for x in m))

    def test_sin_restricciones(self):
        m = self.mensajes({"sentido": "max", "funcion_objetivo": ["1", "2", ""], "restricciones": []})
        self.assertTrue(any("restricción" in x for x in m))

    def test_rechaza_nan_infinito_y_division_por_cero(self):
        for malo in ("nan", "inf", "1/0"):
            m = self.mensajes(problema("max", [malo, "2", ""], [(["1", "2", ""], "<=", "5")]))
            self.assertTrue(any("no es un número" in x for x in m), malo)

    def test_reporta_todos_los_errores_juntos(self):
        m = self.mensajes(problema("max", ["", "x", ""], [(["1", "", ""], "<=", "")]))
        self.assertGreaterEqual(len(m), 4)


if __name__ == "__main__":
    unittest.main()
