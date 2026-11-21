from .base import ModeloPL, Restriccion


def crear_modelo(sentido, c, restricciones):
    """Crea el modelo; el número de variables es la longitud de la función objetivo."""
    return ModeloPL(sentido, c, restricciones)
