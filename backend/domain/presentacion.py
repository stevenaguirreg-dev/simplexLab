"""Convierte números del dominio (fracciones, a + bM) en texto listo para enviar al front."""
from fractions import Fraction

from .numeros import GranM


def a_texto(objeto):
    """Recorre diccionarios y listas pasando los números a texto exacto ('5/2', '-3M + 2/5')."""
    if isinstance(objeto, (Fraction, GranM)):
        return str(objeto)
    if isinstance(objeto, dict):
        return {k: a_texto(v) for k, v in objeto.items()}
    if isinstance(objeto, (list, tuple)):
        return [a_texto(v) for v in objeto]
    return objeto
