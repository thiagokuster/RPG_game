import socket
import tempfile
import unittest
from pathlib import Path

from online.protocol import receive_message
from online.server import LobbyServer


class TestIntegracaoPrivate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "rooms.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def _make_server(state_path):
        return LobbyServer(state_path=state_path)

    def test_ataque_rejeita_alvo_morto(self):
        server = self._make_server(self.state_path)
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 1"})
            reproducao = server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 1"})
            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 1",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            room = server.room_state["Sala 1"]
            room["match"].jogadores[1].hp = 0
            room["match"].jogadores = [room["match"].jogadores[0], room["match"].jogadores[1]]

            response = server._handle_action(conn_a, {"type": "action", "action": "attack", "target": "Bob"})
            self.assertIsNone(response)
            self.assertEqual(room["current_turn"], conn_a)
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_partida_encerrada_rejeita_acao(self):
        server = self._make_server(self.state_path)
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 2"})
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 2"})
            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 2",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            room = server.room_state["Sala 2"]
            room["status"] = "finished"
            room["current_turn"] = conn_a

            response = server._handle_action(conn_a, {"type": "action", "action": "attack", "target": "Bob"})
            self.assertIsNone(response)
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_acao_invalida_retorna_erro(self):
        server = self._make_server(self.state_path)
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            peer_a.settimeout(0.5)
            peer_b.settimeout(0.5)

            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 3"})
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 3"})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 3",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            receive_message(peer_a)
            receive_message(peer_b)

            server._handle_action(conn_a, {"type": "action", "action": "dance", "target": "Bob"})
            payload = None
            while payload is None or payload.get("type") != "error":
                payload = receive_message(peer_a)
                if payload is None:
                    break
            self.assertEqual(payload["type"], "error")
            self.assertEqual(payload["message"], "Acao invalida.")
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_persistencia_salva_e_recupera_salas(self):
        server = self._make_server(self.state_path)
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 4"})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 4"})
            receive_message(peer_b)
            receive_message(peer_a)
            server.save_state()
            recovered = LobbyServer(state_path=self.state_path)
            recovered.load_state()
            self.assertIn("Sala 4", recovered.room_state)
            self.assertEqual(recovered.room_state["Sala 4"]["players"], ["Alice", "Bob"])
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()


if __name__ == "__main__":
    unittest.main()
