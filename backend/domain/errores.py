"""Errores propios del dominio. Se convierten en mensajes claros para el usuario."""


class ErrorDeDominio(Exception):
    """Clase base de todos los errores controlados de la aplicación."""


class ProblemaInvalidoError(ErrorDeDominio):
    """El problema ingresado tiene errores. Guarda la lista completa de mensajes."""

    def __init__(self, mensajes):
        self.mensajes = list(mensajes)
        super().__init__("; ".join(self.mensajes))


class LimiteIteracionesError(ErrorDeDominio):
    """El método superó el máximo de iteraciones permitido."""


class MatrizSingularError(ErrorDeDominio):
    """Se intentó invertir una matriz que no tiene inversa."""
