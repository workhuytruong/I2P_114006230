from server.playerHandler import PlayerHandler

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json
import threading
import time

PORT = 8989

PLAYER_HANDLER = PlayerHandler()
PLAYER_HANDLER.start()

# Simple in-memory chat log
CHAT_LOCK = threading.Lock()
CHAT_LOG: list[dict] = []
NEXT_CHAT_ID = 0
    
class Handler(BaseHTTPRequestHandler):
    # def log_message(self, fmt, *args):
    #     return

    def do_GET(self):
        if self.path == "/":
            self._json(200, {"status": "ok"})
            return
            
        if self.path == "/register":
            pid = PLAYER_HANDLER.register()
            self._json(200, {"message": "registration successful", "id": pid})
            return

        if self.path == "/players":
            self._json(200, {"players": PLAYER_HANDLER.list_players()})
            return

        if self.path.startswith("/chat"):
            self._handle_get_chat()
            return

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/chat":
            self._handle_post_chat()
            return

        if self.path != "/players":
            self._json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid_json"})
            return

        missing = [k for k in ("id", "x", "y", "map") if k not in data]
        if missing:
            self._json(400, {"error": "bad_fields", "missing": missing})
            return

        try:
            pid = int(data["id"])
            x = float(data["x"])
            y = float(data["y"])
            map_name = str(data["map"])
            direction = str(data.get("direction", "DOWN"))
            moving = bool(data.get("moving", False))
        except (ValueError, TypeError):
            self._json(400, {"error": "bad_fields"})
            return

        ok = PLAYER_HANDLER.update(pid, x, y, map_name, direction, moving)
        if not ok:
            self._json(404, {"error": "player_not_found"})
            return

        self._json(200, {"success": True})

    # Utility for JSON responses
    def _json(self, code: int, obj: object) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ------------------- Chat -------------------
    def _handle_post_chat(self):
        global NEXT_CHAT_ID
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid_json"})
            return

        if "id" not in data or "text" not in data:
            self._json(400, {"error": "bad_fields"})
            return
        try:
            pid = int(data["id"])
            text = str(data["text"]).strip()
        except Exception:
            self._json(400, {"error": "bad_fields"})
            return
        if not text:
            self._json(400, {"error": "empty_text"})
            return

        with CHAT_LOCK:
            msg = {"id": NEXT_CHAT_ID, "from": pid, "text": text, "ts": time.time()}
            CHAT_LOG.append(msg)
            NEXT_CHAT_ID += 1
            if len(CHAT_LOG) > 200:
                CHAT_LOG[:] = CHAT_LOG[-200:]
        self._json(200, {"success": True, "msg": msg})

    def _handle_get_chat(self):
        qs = parse_qs(urlparse(self.path).query or "")
        try:
            since = int(qs.get("since", ["-1"])[0])
        except ValueError:
            since = -1
        try:
            limit = int(qs.get("limit", ["50"])[0])
            limit = max(1, min(200, limit))
        except ValueError:
            limit = 50

        with CHAT_LOCK:
            msgs = [m for m in CHAT_LOG if m["id"] > since]
            msgs = msgs[-limit:]
        self._json(200, {"messages": msgs})

if __name__ == "__main__":
    print(f"[Server] Running on localhost with port {PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
