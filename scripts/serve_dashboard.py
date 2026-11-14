"""
Obre el dashboard al navegador (Windows, Mac i Linux):
    python scripts/serve_dashboard.py
Cal un servidor local perque el navegador carregui els moduls de JavaScript.
"""
import functools
import http.server
import webbrowser
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "dashboard"


class Handler(http.server.SimpleHTTPRequestHandler):
    # a Windows el tipus dels .js de vegades surt malament; el forcem
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".woff2": "font/woff2", ".svg": "image/svg+xml"}

    def end_headers(self):
        # que el navegador no guardi res: aixi sempre es veu l'ultima versio despres d'un git pull
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def start():
    handler = functools.partial(Handler, directory=str(FOLDER))
    # si el port ja l'ocupa un servidor antic, en provem un altre
    for port in range(8000, 8011):
        try:
            return http.server.ThreadingHTTPServer(("127.0.0.1", port), handler), port
        except OSError:
            print(f"El port {port} esta ocupat (potser hi ha un dashboard antic obert). Provo el seguent...")
    raise SystemExit("No hi ha cap port lliure entre 8000 i 8010. Tanqueu les altres terminals i torneu-ho a provar.")


if __name__ == "__main__":
    server, port = start()
    url = f"http://localhost:{port}"
    print(f"Dashboard a {url}  (Ctrl + C per parar)")
    webbrowser.open(url)
    with server:
        server.serve_forever()
