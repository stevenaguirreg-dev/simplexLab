"""Ciclo común del simplex. Gran M y simplex revisado solo cambian cómo guardan el estado.

Como ambos usan las mismas reglas de entrada/salida, recorren las mismas bases.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List

from ..errores import LimiteIteracionesError
from ..pivoteo import elegir_entrante, prueba_razon

OPTIMO, NO_ACOTADO, INFACTIBLE = "optimo", "no_acotado", "infactible"
LIMITE_ITERACIONES = 500


@dataclass
class ResultadoSimplex:
    estado: str
    base: List[int]
    x: List[Fraction]                 # valor de todas las variables de la forma estándar
    z_max: object                     # valor de Z en la forma Max (GranM)
    iteraciones: int
    pasos: List[dict] = field(default_factory=list)
    instantanea_final: dict = None
    secuencia_bases: List[tuple] = field(default_factory=list)
    iteraciones_con_empate: List[int] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)


class ResolutorSimplex(ABC):
    nombre = ""

    def __init__(self, forma, registrar_pasos=True):
        self.forma = forma
        self.registrar_pasos = registrar_pasos
        self.base = list(forma.base_inicial)

    # ---- estado propio de cada método -------------------------------------
    @abstractmethod
    def _iniciar(self):
        """Prepara tablero o B^-1 con la base inicial."""

    @abstractmethod
    def _costos_reducidos(self):
        """Lista d_j = z_j - c_j para todas las variables (renglón 0)."""

    @abstractmethod
    def _columna(self, j):
        """Columna de la variable j expresada en la base actual (B^-1 a_j)."""

    @abstractmethod
    def _xb(self):
        """Valores de las variables básicas (B^-1 b)."""

    @abstractmethod
    def _valor_z(self):
        """Valor actual de Z en la forma Max."""

    @abstractmethod
    def _pivotar(self, fila, columna):
        """Hace el cambio de base y actualiza self.base."""

    @abstractmethod
    def _instantanea(self):
        """Foto del estado actual para mostrar paso a paso."""

    # ---- ciclo común --------------------------------------------------------
    def resolver(self):
        f = self.forma
        self._iniciar()
        pasos, empates, advertencias = [], [], []
        secuencia = [tuple(self.base)]
        iteracion, sin_mejora, usar_bland = 0, 0, False
        umbral = f.N + f.m
        z_anterior = self._valor_z()
        estado = OPTIMO

        while True:
            if iteracion > LIMITE_ITERACIONES:
                raise LimiteIteracionesError(
                    f"Se superaron {LIMITE_ITERACIONES} iteraciones sin llegar a una solución."
                )
            d = self._costos_reducidos()
            fuera_de_base = set(range(f.N)) - set(self.base)
            candidatos = [j for j in sorted(fuera_de_base) if not f.es_artificial(j)]
            entrante, empate_entrante = elegir_entrante(d, candidatos, usar_bland)
            if entrante is None:
                break

            alfa = self._columna(entrante)
            fila, razones, empate = prueba_razon(self._xb(), alfa, self.base)
            if self.registrar_pasos:
                negativos = sorted((j for j in candidatos if d[j] < 0), key=lambda j: (d[j], j))
                pasos.append({
                    "numero": iteracion,
                    "instantanea": self._instantanea(),
                    "entrante": {
                        "indice": entrante,
                        "nombre": f.nombres[entrante],
                        "costo": d[entrante],
                        "criterio": "bland" if usar_bland else "mas_negativo",
                        "empate": empate_entrante,
                        "candidatos": [{"nombre": f.nombres[j], "costo": d[j]} for j in negativos],
                    },
                    "columna_entrante": alfa,
                    "razones": [
                        {**r, "variable_basica": f.nombres[r["variable_basica"]]} for r in razones
                    ],
                    "saliente": None if fila is None else {"fila": fila, "nombre": f.nombres[self.base[fila]]},
                    "pivote": None if fila is None else alfa[fila],
                    "empate_razon": empate,
                })
            if fila is None:
                estado = NO_ACOTADO
                break
            if empate:
                empates.append(iteracion)
            self._pivotar(fila, entrante)
            iteracion += 1
            secuencia.append(tuple(self.base))
            z = self._valor_z()
            sin_mejora = sin_mejora + 1 if z == z_anterior else 0
            z_anterior = z
            if not usar_bland and sin_mejora >= umbral:
                usar_bland = True
                advertencias.append(
                    "Se detectaron muchas iteraciones sin mejorar Z; se activó la regla de Bland para evitar ciclos."
                )

        xb = self._xb()
        x = [Fraction(0)] * f.N
        for i, j in enumerate(self.base):
            x[j] = xb[i]
        artificial_positiva = any(f.es_artificial(j) and xb[i] > 0 for i, j in enumerate(self.base))

        if estado == OPTIMO and artificial_positiva:
            estado = INFACTIBLE
        elif estado == NO_ACOTADO and artificial_positiva:
            # Con una artificial positiva no se sabe si el problema es no acotado o infactible: se prueba la factibilidad.
            auxiliar = type(self)(f.con_objetivo_cero(), registrar_pasos=False).resolver()
            if auxiliar.estado != OPTIMO or any(
                f.es_artificial(j) and auxiliar.x[j] > 0 for j in range(f.N)
            ):
                estado = INFACTIBLE

        return ResultadoSimplex(
            estado=estado,
            base=list(self.base),
            x=x,
            z_max=self._valor_z(),
            iteraciones=iteracion,
            pasos=pasos,
            instantanea_final=self._instantanea() if self.registrar_pasos else None,
            secuencia_bases=secuencia,
            iteraciones_con_empate=empates,
            advertencias=advertencias,
        )
