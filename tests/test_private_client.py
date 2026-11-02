import socket
import tempfile
import unittest
from pathlib import Path

from equipamento import Equipamento
from online.server import LobbyServer
from private.client import GameClient


class TestPrivateClient(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "rooms.json"
        self.server = LobbyServer(state_path=self.state_path)
        self.conn, self.peer = socket.socketpair()

    def tearDown(self):
        self.conn.close()
        self.peer.close()
        self.temp_dir.cleanup()

    def _join_room(self, client):
        client.socket = self.conn
        client.connected = True
        self.server._handle_join(self.conn, {"type": "join", "player": client.player, "room": client.room})
        return client

    def test_comando_attack_envia_alvo_e_retorna_resposta(self):
        client = GameClient(player="Alice", room="Sala privada")
        self._join_room(client)
        other_conn, other_peer = socket.socketpair()
        try:
            self.server._handle_join(other_conn, {"type": "join", "player": "Bob", "room": "Sala privada"})
            self.server._handle_message(self.conn, {
                "type": "start_match",
                "room": "Sala privada",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            self.conn.settimeout(0.5)
            other_conn.settimeout(0.5)
            self.server._handle_action(self.conn, {"type": "action", "action": "attack", "target": "Bob"})

            response = client.parse_command("attack Bob")
            self.assertEqual(response["action"], "attack")
            self.assertEqual(response["target"], "Bob")
        finally:
            other_conn.close()
            other_peer.close()

    def test_comando_shop_compra_item_da_loja(self):
        client = GameClient(player="Alice", room="Sala privada")
        self._join_room(client)
        other_conn, other_peer = socket.socketpair()
        try:
            self.server._handle_join(other_conn, {"type": "join", "player": "Bob", "room": "Sala privada"})
            self.server._handle_message(self.conn, {
                "type": "start_match",
                "room": "Sala privada",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            jogador = self.server.room_state["Sala privada"]["match"].jogadores[0]
            item = Equipamento.gerarEquipamento(1)
            self.server.room_state["Sala privada"]["shop"] = [item]

            command = client.parse_command("buy 0")
            self.assertEqual(command["action"], "buy")
            self.assertEqual(command["item_index"], 0)
        finally:
            other_conn.close()
            other_peer.close()

    def test_comando_invalido_retorna_erro_de_uso(self):
        client = GameClient(player="Alice", room="Sala privada")

        with self.assertRaisesRegex(ValueError, "Comando invalido"):
            client.parse_command("acao inexistente")
