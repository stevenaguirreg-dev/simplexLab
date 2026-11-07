"""Servidor HTTP: expone /api/resolver y sirve la interfaz (carpeta frontend) en el mismo puerto."""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from services.servicio_resolucion import ServicioResolucion

from .esquemas import leer_solicitud, MAX_BYTES
from .manejo_errores import respuesta_de_error

CARPETA_FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
servicio = ServicioResolucion()


class ManejadorHTTP(BaseHTTPRequestHandler):
    server_version = "SimplexOpt/1.0"

    def log_message(self, formato, *args):  # registro corto en consola
        print(f"[{self.log_date_time_string()}] {formato % args}")

    # ---- utilidades ---------------------------------------------------------
    def _enviar_json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _enviar_archivo(self, ruta_url):
        relativa = "index.html" if ruta_url in ("", "/") else ruta_url.lstrip("/")
        ruta = (CARPETA_FRONTEND / relativa).resolve()
        if CARPETA_FRONTEND.resolve() not in ruta.parents or not ruta.is_file():
            self._enviar_json(404, {"ok": False, "errores": ["Página no encontrada."]})
            return
        tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript", "application/json"):
            tipo += "; charset=utf-8"
        datos = ruta.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(datos)

    # ---- rutas --------------------------------------------------------------
    def do_GET(self):
        ruta = self.path.split("?", 1)[0]
        if ruta == "/api/salud":
            self._enviar_json(200, {"estado": "activo"})
        else:
            self._enviar_archivo(ruta)

    def do_POST(self):
        ruta = self.path.split("?", 1)[0]
        if ruta != "/api/resolver":
            self._enviar_json(404, {"ok": False, "errores": ["Ruta no encontrada."]})
            return
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            cuerpo = self.rfile.read(min(largo, MAX_BYTES + 1))
            solicitud = leer_solicitud(cuerpo)
            self._enviar_json(200, servicio.resolver(solicitud))
        except Exception as error:  # todo error se traduce a un mensaje claro
            codigo, cuerpo_error = respuesta_de_error(error)
            self._enviar_json(codigo, cuerpo_error)


def iniciar_servidor(puerto=8080, host="0.0.0.0"):
    servidor = ThreadingHTTPServer((host, puerto), ManejadorHTTP)
    print(f"SimplexOpt listo en http://localhost:{puerto}  (Ctrl+C para detener)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
