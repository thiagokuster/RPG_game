import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.events import EventBus
from web.limits import MAX_BODY, RateLimiter, sanitize_name, sanitize_password, sanitize_room
from web.lobby import Lobby

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

lobby = Lobby()
events = EventBus()
limiter = RateLimiter(limit=60, window=10)
join_limiter = RateLimiter(limit=8, window=60)


class LobbyRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _safe_path(self, url_path):
        relative = url_path.lstrip("/")
        if relative in {"", "index.html"}:
            relative = "index.html"
        elif relative in {"jogo", "jogo.html"}:
            relative = "jogo.html"
        candidate = (FRONTEND_DIR / relative).resolve()
        root = FRONTEND_DIR.resolve()
        if root != candidate and root not in candidate.parents:
            return None
        return candidate if candidate.is_file() else None

    def _send_file(self, path):
        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _publish(self, room_code):
        if not room_code:
            return
        try:
            events.publish(str(room_code).upper(), lobby.get_room(room_code)["room"])
        except KeyError:
            return

    def _stream_room(self, room_code):
        room_name = (room_code or "").strip().upper()
        try:
            snapshot = lobby.get_room(room_name)["room"]
        except KeyError as exc:
            self._send_json({"error": str(exc)}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        queue = events.subscribe(room_name)
        try:
            self.wfile.write(f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()
            while True:
                payload = queue.get()
                self.wfile.write(f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        finally:
            events.unsubscribe(room_name, queue)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not limiter.check(self.client_address[0]):
            self._send_json({"error": "Muitas requisições. Tente novamente em instantes."}, 429)
            return
        if parsed.path == "/api/rooms":
            self._send_json(lobby.list_rooms())
            return
        if parsed.path == "/api/room":
            code = parse_qs(parsed.query).get("code", [""])[0]
            try:
                self._send_json(lobby.get_room(sanitize_room(code)))
            except (KeyError, ValueError) as exc:
                self._send_json({"error": str(exc)}, 404 if isinstance(exc, KeyError) else 400)
            return
        if parsed.path == "/api/stream":
            code = parse_qs(parsed.query).get("code", [""])[0]
            try:
                self._stream_room(sanitize_room(code))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
            return

        path = self._safe_path(parsed.path)
        if path is None:
            self._send_json({"error": "Endpoint não encontrado."}, 404)
            return
        self._send_file(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if not limiter.check(self.client_address[0]):
            self._send_json({"error": "Muitas requisições. Tente novamente em instantes."}, 429)
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > MAX_BODY:
            self._send_json({"error": "Requisição grande demais."}, 400)
            return
        raw_body = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Body inválido."}, 400)
            return
        if not isinstance(payload, dict):
            self._send_json({"error": "Body inválido."}, 400)
            return

        try:
            if parsed.path == "/api/create-room":
                result = lobby.create_room(
                    sanitize_name(payload.get("player", "")),
                    password=sanitize_password(payload.get("password")),
                )
                self._send_json(result)
                self._publish(result.get("code"))
                return
            if parsed.path == "/api/join-room":
                if not join_limiter.check(self.client_address[0]):
                    self._send_json({"error": "Muitas tentativas de entrada. Aguarde um pouco."}, 429)
                    return
                result = lobby.join_room(
                    sanitize_name(payload.get("player", "")),
                    sanitize_room(payload.get("room", "")),
                    password=sanitize_password(payload.get("password")),
                )
                self._send_json(result)
                self._publish(result.get("code"))
                return
            if parsed.path == "/api/start-match":
                result = lobby.start_match(
                    payload.get("room", ""),
                    payload.get("classes", {}),
                    token=payload.get("token"),
                    modo=payload.get("modo", "pvp"),
                )
                self._send_json(result)
                self._publish(result.get("code"))
                return
            if parsed.path == "/api/action":
                result = lobby.perform_action(
                    payload.get("room", ""),
                    action=payload.get("action", "attack"),
                    target=payload.get("target"),
                    item_index=payload.get("item_index"),
                    action_type=payload.get("action_type"),
                    magic=payload.get("magic"),
                    token=payload.get("token"),
                )
                self._send_json(result)
                if not result.get("error") and result.get("type") != "error":
                    self._publish(result.get("room") or payload.get("room"))
                return
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            self._send_json({"error": str(exc) or "Requisição inválida."}, 400)
            return

        self._send_json({"error": "Endpoint não encontrado."}, 404)

    def log_message(self, format, *args):
        return


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Backend HTTP do Arena RPG, com frontend separado.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.host in {"0.0.0.0", "::"}:
        print("Aviso: o servidor está escutando em todas as interfaces. Use só em rede confiável.")
    server = ThreadingHTTPServer((args.host, args.port), LobbyRequestHandler)
    print(f"Frontend em http://{args.host}:{args.port}")
    print(f"Arquivos em {FRONTEND_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
