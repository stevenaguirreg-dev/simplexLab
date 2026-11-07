"""Convierte cualquier error en una respuesta JSON con mensajes comprensibles."""
import sys
import traceback

from domain.errores import ErrorDeDominio, ProblemaInvalidoError


def respuesta_de_error(error):
    """Devuelve (código_http, cuerpo_json). Nunca expone trazas al usuario."""
    if isinstance(error, ProblemaInvalidoError):
        return 400, {"ok": False, "errores": error.mensajes}
    if isinstance(error, ErrorDeDominio):
        return 422, {"ok": False, "errores": [str(error)]}
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    return 500, {"ok": False, "errores": ["Ocurrió un error inesperado al resolver el problema. Revise los datos e intente de nuevo."]}
