"""Orquesta todo el flujo: validar, resolver, analizar y armar la respuesta."""
from fractions import Fraction

from domain.casos_especiales import alternativos_para_salida, detectar_casos_optimos
from domain.errores import ProblemaInvalidoError
from domain.forma_estandar import construir_forma_estandar
from domain.numeros import numero_final
from domain.presentacion import a_texto
from domain.resolutores import INFACTIBLE, NO_ACOTADO, OPTIMO, RESOLUTORES
from domain.sensibilidad import analizar_sensibilidad
from domain.validacion import validar_problema

MODOS = ("inmediata", "paso_a_paso")
MENSAJES = {
    OPTIMO: "Solución óptima encontrada.",
    INFACTIBLE: "El problema no tiene solución factible.",
    NO_ACOTADO: "La solución es no acotada: Z puede mejorar indefinidamente sin violar las restricciones.",
}


class ServicioResolucion:
    def resolver(self, solicitud):
        metodo = solicitud.get("metodo")
        modo = solicitud.get("modo")
        errores = []
        if metodo not in RESOLUTORES:
            errores.append("Elija un método de solución: Gran M o Revisado.")
        if modo not in MODOS:
            errores.append("El modo debe ser 'inmediata' o 'paso_a_paso'.")
        if errores:
            raise ProblemaInvalidoError(errores)

        modelo = validar_problema(solicitud.get("problema"))
        forma = construir_forma_estandar(modelo)
        paso_a_paso = modo == "paso_a_paso"
        resultado = RESOLUTORES[metodo](forma, registrar_pasos=paso_a_paso).resolver()

        respuesta = {
            "ok": True,
            "metodo": metodo,
            "modo": modo,
            "modelo": {
                "num_variables": modelo.num_variables,
                "puede_graficar": modelo.puede_graficar,
                "objetivo": modelo.texto_objetivo(),
                "restricciones": modelo.texto_restricciones(),
            },
            "estado": resultado.estado,
            "mensaje": MENSAJES[resultado.estado],
            "iteraciones": resultado.iteraciones,
            "advertencias": list(resultado.advertencias),
            "casos_especiales": {"degenerado": False, "optimos_multiples": False, "mensajes": []},
            "solucion": None,
        }

        z_original = None
        optimos = []
        if resultado.estado == OPTIMO:
            n = modelo.num_variables
            x = resultado.x[:n]
            z_original = sum((modelo.c[j] * x[j] for j in range(n)), Fraction(0))
            casos = detectar_casos_optimos(modelo, forma, resultado)
            optimos = [x] + casos["optimos_alternativos"]
            respuesta["casos_especiales"] = {
                "degenerado": casos["degenerado"],
                "variables_basicas_en_cero": casos["variables_basicas_en_cero"],
                "optimos_multiples": casos["optimos_multiples"],
                "rayo_optimo": casos["rayo_optimo"],
                "mensajes": casos["mensajes"],
            }
            respuesta["solucion"] = {
                "z": numero_final(z_original),
                "variables": [{"nombre": modelo.nombres[j], "valor": numero_final(x[j])} for j in range(n)],
                "restricciones": self._estado_restricciones(modelo, x),
                "base_final": [forma.nombres[j] for j in resultado.base],
                "optimos_alternativos": alternativos_para_salida(casos),
            }

        if not paso_a_paso:
            return respuesta

        respuesta["forma_estandar"] = {
            "transformaciones": forma.transformaciones,
            "objetivo": forma.objetivo_texto,
            "ecuaciones": forma.ecuaciones,
            "variables": [{"nombre": nombre, "tipo": tipo} for nombre, tipo in zip(forma.nombres, forma.tipos)],
            "base_inicial": [forma.nombres[j] for j in forma.base_inicial],
            "etiqueta_z": forma.etiqueta_z,
        }
        respuesta["pasos"] = a_texto(resultado.pasos)
        respuesta["instantanea_final"] = a_texto(resultado.instantanea_final)
        respuesta["iteraciones_con_empate"] = resultado.iteraciones_con_empate
        respuesta["grafico"] = modelo.analisis_grafico(
            {"estado": resultado.estado, "z": z_original, "optimos": optimos}
        )
        if resultado.estado == OPTIMO:
            respuesta["sensibilidad"] = analizar_sensibilidad(modelo, forma, resultado.base)
        respuesta["comparacion"] = self._comparar(metodo, forma, resultado)
        return respuesta

    @staticmethod
    def _estado_restricciones(modelo, x):
        salida = []
        for i, r in enumerate(modelo.restricciones, start=1):
            lhs = sum((a * v for a, v in zip(r.coeficientes, x)), Fraction(0))
            if r.relacion == "<=":
                tipo, valor = "holgura", r.rhs - lhs
            elif r.relacion == ">=":
                tipo, valor = "exceso", lhs - r.rhs
            else:
                tipo, valor = "igualdad", Fraction(0)
            salida.append({
                "numero": i,
                "relacion": r.relacion,
                "lhs": numero_final(lhs),
                "rhs": numero_final(r.rhs),
                "tipo": tipo,
                "valor": numero_final(valor),
                "activa": valor == 0,
            })
        return salida

    @staticmethod
    def _comparar(metodo, forma, resultado):
        """Resuelve también con el otro método y compara resultados (verificación cruzada)."""
        otro = "revisado" if metodo == "gran_m" else "gran_m"
        try:
            alterno = RESOLUTORES[otro](forma, registrar_pasos=False).resolver()
        except Exception as error:  # la comparación nunca debe tumbar la respuesta principal
            return {"metodo_alterno": otro, "disponible": False, "detalle": f"No se pudo comparar: {error}"}
        return {
            "metodo_alterno": otro,
            "disponible": True,
            "mismo_estado": alterno.estado == resultado.estado,
            "mismo_z": alterno.z_max == resultado.z_max if resultado.estado == OPTIMO else None,
            "misma_base_final": alterno.base == resultado.base,
            "misma_secuencia_de_bases": alterno.secuencia_bases == resultado.secuencia_bases,
            "iteraciones": {metodo: resultado.iteraciones, otro: alterno.iteraciones},
        }
