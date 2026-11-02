import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from web.site import FRONTEND_DIR, LobbyRequestHandler, lobby


class TestFrontendBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LobbyRequestHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return response.status, response.headers.get_content_type(), response.read()

    def _post(self, path, payload):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_frontend_separado_do_backend(self):
        self.assertTrue((FRONTEND_DIR / "index.html").is_file())
        self.assertTrue((FRONTEND_DIR / "jogo.html").is_file())
        self.assertTrue((FRONTEND_DIR / "js" / "api.js").is_file())

        status, content_type, body = self._get("/")
        html = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "text/html")
        self.assertIn("/js/lobby.js", html)
        self.assertIn("rpg_token", (FRONTEND_DIR / "js" / "lobby.js").read_text(encoding="utf-8"))
        self.assertIn("token", (FRONTEND_DIR / "js" / "api.js").read_text(encoding="utf-8"))
        self.assertNotIn("def create_room", html)

        status, content_type, board = self._get("/jogo.html")
        self.assertEqual(status, 200)
        self.assertIn("Seu lance", board.decode("utf-8"))

        status, content_type, css = self._get("/css/app.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", content_type)
        self.assertIn("--bg", css.decode("utf-8"))

    def test_backend_cria_sala_e_envia_estado(self):
        status, created = self._post("/api/create-room", {"player": "Ana"})
        self.assertEqual(status, 200)
        self.assertEqual(created["players"][0]["name"], "Ana")
        code = created["code"]

        status, joined = self._post("/api/join-room", {"player": "Bruno", "room": code})
        self.assertEqual(status, 200)
        self.assertEqual(len(joined["players"]), 2)

        status, started = self._post("/api/start-match", {
            "room": code,
            "classes": {"Ana": "Guerreiro", "Bruno": "Mago"},
            "token": created["token"],
        })
        self.assertEqual(status, 200)
        self.assertEqual(started["status"], "started")
        self.assertEqual(started["current_turn"], "Ana")
        self.assertTrue(started["log"])

        room = lobby.get_room(code)["room"]
        self.assertEqual(room["code"], code)
        bruno = next(player for player in room["players"] if player["name"] == "Bruno")
        self.assertTrue(bruno["magias"])
        self.assertTrue(created["token"])
        self.assertTrue(joined["token"])
        self.assertNotEqual(created["token"], joined["token"])

    def test_start_e_acao_exigem_token_do_jogador(self):
        status, created = self._post("/api/create-room", {"player": "AnaAuth"})
        code = created["code"]
        status, joined = self._post("/api/join-room", {"player": "BrunoAuth", "room": code})
        self.assertEqual(status, 200)

        with self.assertRaises(urllib.error.HTTPError) as contexto:
            self._post("/api/start-match", {
                "room": code,
                "classes": {"AnaAuth": "Guerreiro", "BrunoAuth": "Mago"},
            })
        self.assertEqual(contexto.exception.code, 400)

        with self.assertRaises(urllib.error.HTTPError) as contexto:
            self._post("/api/start-match", {
                "room": code,
                "classes": {"AnaAuth": "Guerreiro", "BrunoAuth": "Mago"},
                "token": joined["token"],
            })
        self.assertEqual(contexto.exception.code, 400)

        status, started = self._post("/api/start-match", {
            "room": code,
            "classes": {"AnaAuth": "Guerreiro", "BrunoAuth": "Mago"},
            "token": created["token"],
        })
        self.assertEqual(status, 200)

        with self.assertRaises(urllib.error.HTTPError) as contexto:
            self._post("/api/action", {"room": code, "player": "AnaAuth", "action": "attack", "target": "BrunoAuth"})
        self.assertEqual(contexto.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
