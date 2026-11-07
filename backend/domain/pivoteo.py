"""Reglas de pivoteo comunes a los dos métodos (Gran M y simplex revisado)."""
from fractions import Fraction


def elegir_entrante(costos, candidatos, usar_bland=False):
    """Variable que entra: la de costo reducido más negativo (regla de clase).

    Empates: menor índice. Si usar_bland=True se toma siempre el menor índice
    con costo negativo (evita ciclos). Devuelve (índice, hay_empate) o (None, False).
    """
    negativos = [j for j in candidatos if costos[j] < 0]
    if not negativos:
        return None, False
    if usar_bland:
        return min(negativos), False
    minimo = min(costos[j] for j in negativos)
    empatados = [j for j in negativos if costos[j] == minimo]
    return min(empatados), len(empatados) > 1


def prueba_razon(xb, columna, base):
    """Prueba de la razón mínima. Solo cuentan los coeficientes estrictamente positivos.

    Devuelve (fila_saliente | None, detalle_por_fila, hay_empate).
    Empates: sale la variable básica de menor índice.
    """
    detalle = []
    mejor = None
    mejor_razon = None
    empate = False
    for i, (valor, alfa) in enumerate(zip(xb, columna)):
        razon = Fraction(valor) / alfa if alfa > 0 else None
        detalle.append({"fila": i, "variable_basica": base[i], "columna": alfa, "xb": valor, "razon": razon})
        if razon is None:
            continue
        if mejor is None or razon < mejor_razon:
            mejor, mejor_razon, empate = i, razon, False
        elif razon == mejor_razon:
            empate = True
            if base[i] < base[mejor]:
                mejor = i
    return mejor, detalle, empate
