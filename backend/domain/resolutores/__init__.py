from .base import INFACTIBLE, NO_ACOTADO, OPTIMO, ResultadoSimplex, ResolutorSimplex
from .gran_m import ResolutorGranM
from .revisado import ResolutorRevisado

RESOLUTORES = {"gran_m": ResolutorGranM, "revisado": ResolutorRevisado}
