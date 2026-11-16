"""Read-only loopback dashboard; never executes task content."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from core import Error

UI = Path(__file__).resolve().parent.parent / "ui"


def make_server(store, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, code, content, mime):
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if self.headers.get("Host") not in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"):
                self.respond(403, b"Loopback host required", "text/plain")
                return
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                self.respond(403, b"Cross-origin access refused", "text/plain")
                return
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/api/tasks":
                    value = store.list()
                elif path.startswith("/api/tasks/"):
                    parts = path.split("/")
                    task = store.task(parts[3])
                    if len(parts) == 4:
                        value = task.view()
                    elif len(parts) == 6 and parts[4] == "artifacts":
                        reference = next((a for a in task.load()["artifacts"] if a["path"].split("/")[-1] == parts[5]), None)
                        if reference is None:
                            raise Error("Unknown artifact")
                        value = {"text": task.read_blob(reference).decode("utf-8")}
                    elif len(parts) == 6 and parts[4] == "diffs":
                        candidate = next((c for c in task.load()["candidates"] if c["id"] == parts[5]), None)
                        if candidate is None:
                            raise Error("Unknown candidate")
                        value = {"text": task.read_blob(candidate["diff"]).decode("utf-8", errors="replace")}
                    elif len(parts) == 6 and parts[4] == "evidence":
                        evidence = next((e for r in task.load()["runs"] for e in r["evidence"] if e["id"] == parts[5]), None)
                        if evidence is None:
                            raise Error("Unknown evidence")
                        value = {"text": task.read_blob(evidence).decode("utf-8", errors="replace")}
                    else:
                        raise Error("Unknown route")
                elif path in ("/", "/app.js", "/style.css"):
                    name = "index.html" if path == "/" else path[1:]
                    mime = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8"}[name]
                    self.respond(200, (UI / name).read_bytes(), mime)
                    return
                else:
                    raise Error("Unknown route")
                self.respond(200, json.dumps(value).encode(), "application/json")
            except (Error, OSError, ValueError, KeyError) as error:
                self.respond(404, json.dumps({"error": str(error)}).encode(), "application/json")

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(store, port=0):
    server = make_server(store, port)
    print(json.dumps({"url": f"http://127.0.0.1:{server.server_port}/", "read_only": True}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
