from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from transport_solver import SolverError, solve_transport_problem

ROOT = Path(__file__).resolve().parents[1]


class TransportRequestHandler(BaseHTTPRequestHandler):
    server_version = "TransportSolverPython/1.0"

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json({"ok": True})
            return

        requested = self.path.split("?", 1)[0]
        if requested == "/":
            requested = "/index.html"
        relative = unquote(requested).lstrip("/")
        target = (ROOT / relative).resolve()

        if not str(target).startswith(str(ROOT)) or not target.is_file():
            self.send_error(404, "Nie znaleziono pliku")
            return

        content_type, _ = mimetypes.guess_type(str(target))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def do_POST(self) -> None:
        if self.path != "/api/solve":
            self.send_error(404, "Nie znaleziono endpointu")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = solve_transport_problem(payload)
            self._json(result)
        except json.JSONDecodeError:
            self._json({"success": False, "message": "Niepoprawny JSON."}, status=400)
        except SolverError as exc:
            self._json({"success": False, "message": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._json({"success": False, "message": f"Blad serwera: {exc}"}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend Python dla solvera transportowego.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), TransportRequestHandler)
    print(f"Backend dziala: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
