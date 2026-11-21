"""Punto de entrada. Revisa las librerías, las instala si faltan y arranca la aplicación.

Uso:   python backend/main.py        ->  abre http://localhost:8080
"""
import importlib.util
import os
import subprocess
import sys

# paquete de pip -> nombre del módulo al importarlo
DEPENDENCIAS = {"numpy": "numpy", "sympy": "sympy"}


def verificar_dependencias():
    """Si falta alguna librería, la instala con pip. Un fallo no detiene la app:
    el núcleo del simplex usa solo fracciones de Python (exactitud total)."""
    faltantes = [paquete for paquete, modulo in DEPENDENCIAS.items() if importlib.util.find_spec(modulo) is None]
    if not faltantes:
        print("Librerías verificadas: todo instalado.")
        return
    print(f"Instalando librerías faltantes: {', '.join(faltantes)} ...")
    try:
        # pocos reintentos y poca espera: sin internet no debe quedarse colgada la aplicación
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--retries", "1", "--timeout", "8", *faltantes],
            timeout=45,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as error:
        print(f"Aviso: no se pudieron instalar ({error}). La aplicación continúa sin ellas.")


def main():
    verificar_dependencias()
    from api.rutas import iniciar_servidor  # se importa después para que sys.path ya esté listo

    puerto = int(os.environ.get("PUERTO", "8080"))
    iniciar_servidor(puerto)


if __name__ == "__main__":
    main()
