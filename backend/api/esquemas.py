"""Formato de la solicitud que recibe la API (y del archivo JSON que se carga en el front).

{
  "metodo": "gran_m" | "revisado",
  "modo":   "inmediata" | "paso_a_paso",
  "problema": {
    "sentido": "max" | "min",
    "funcion_objetivo": ["3", "2", "5"],                 # x1, x2, x3 (x3 vacío = 2 variables)
    "restricciones": [
      {"coeficientes": ["1", "2", "1"], "relacion": "<=", "rhs": "430"}
    ]
  }
}
Los números se envían como texto para conservar la exactitud: "0.1", "-3", "1/3".
"""
import json

from domain.errores import ProblemaInvalidoError

MAX_BYTES = 1_000_000


def leer_solicitud(cuerpo_bytes):
    """Convierte el cuerpo HTTP en un diccionario, o lanza un error con mensaje claro."""
    if not cuerpo_bytes:
        raise ProblemaInvalidoError(["La solicitud llegó vacía."])
    if len(cuerpo_bytes) > MAX_BYTES:
        raise ProblemaInvalidoError(["La solicitud es demasiado grande."])
    try:
        datos = json.loads(cuerpo_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProblemaInvalidoError(["La solicitud no es un JSON válido."])
    if not isinstance(datos, dict):
        raise ProblemaInvalidoError(["La solicitud debe ser un objeto JSON."])
    return datos
