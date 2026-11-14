"""
Obre el dashboard al navegador (Windows, Mac i Linux):
    python scripts/serve_dashboard.py
Cal un servidor local perque el navegador carregui els moduls de JavaScript.
"""
import functools
import http.server
import webbrowser
from pathlib import Path

PORT = 8000
FOLDER = Path(__file__).resolve().parents[1] / "dashboard"


class Handler(http.server.SimpleHTTPRequestHandler):
    # a Windows el tipus dels .js de vegades surt malament; el forcem
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".woff2": "font/woff2", ".svg": "image/svg+xml"}

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=str(FOLDER))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        url = f"http://localhost:{PORT}"
        print(f"Dashboard a {url}  (Ctrl + C per parar)")
        webbrowser.open(url)
        server.serve_forever()
