import socket
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from online.protocol import MAX_MESSAGE, decode_message, encode_message, receive_message
from online.server import LobbyServer


class TestOnlineProtocol(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def make_server(self):
        return LobbyServer(state_path=Path(self.temp_dir.name) / "rooms.json")

    def test_encode_decode_round_trip(self):
        payload = {
            "type": "join",
            "player": "Alice",
            "room": "Sala do grupo"
        }
        self.assertEqual(decode_message(encode_message(payload)), payload)

    def test_rejoin_nao_duplica_jogador_na_mesma_sala(self):
        server = self.make_server()
        conn_a, conn_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 1"})
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 1"})

            self.assertEqual(len(server.rooms["Sala 1"]), 1)
            self.assertEqual([server.connections[c]["player"] for c in server.rooms["Sala 1"]], ["Alice"])
        finally:
            conn_a.close()
            conn_b.close()

    def test_turno_avanca_entre_jogadores_na_mesma_sala(self):
        server = self.make_server()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 2"})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 2"})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 2",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"}
            })
            receive_message(peer_a)
            receive_message(peer_b)

            self.assertEqual(server.room_state["Sala 2"]["order"], [conn_a, conn_b])
            self.assertEqual(server.room_state["Sala 2"]["current_turn"], conn_a)

            with patch("jogador.Jogador.d20", return_value=1):
                server._handle_action(conn_a, {"type": "action", "action": "attack", "target": "Bob"})

            self.assertEqual(server.room_state["Sala 2"]["current_turn"], conn_b)
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_list_rooms_retorna_todas_as_salas(self):
        server = self.make_server()
        conn_a, conn_peer = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala A"})
            receive_message(conn_peer)

            outra, outra_peer = socket.socketpair()
            try:
                server._handle_join(outra, {"type": "join", "player": "Bob", "room": "Sala B"})
                receive_message(outra_peer)

                server._handle_list_rooms(conn_a, {})
                rooms_payload = receive_message(conn_peer)

                self.assertEqual(rooms_payload["type"], "rooms")
                self.assertIn("Sala A", rooms_payload["rooms"])
                self.assertIn("Sala B", rooms_payload["rooms"])
            finally:
                outra.close()
                outra_peer.close()
        finally:
            conn_a.close()
            conn_peer.close()

    def test_action_fora_da_vez_retorna_erro(self):
        server = self.make_server()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 3"})
            receive_message(peer_a)
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

            server._handle_action(conn_b, {"type": "action", "action": "attack", "target": "Alice"})
            payload = receive_message(peer_b)

            self.assertEqual(payload["type"], "error")
            self.assertEqual(payload["message"], "Nao e sua vez.")
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_start_match_rejeita_menos_de_dois_jogadores(self):
        server = LobbyServer()
        conn_a, peer_a = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 6"})
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 6",
                "classes": {"Alice": "Guerreiro"}
            })
            payload = receive_message(peer_a)

            self.assertEqual(payload["type"], "error")
            self.assertIn("dois jogadores", payload["message"])
        finally:
            conn_a.close()
            peer_a.close()

    def test_start_match_rejeita_partida_ja_iniciada(self):
        server = LobbyServer()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 7"})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 7"})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 7",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"}
            })
            receive_message(peer_a)
            receive_message(peer_b)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 7",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"}
            })
            payload = receive_message(peer_a)

            self.assertEqual(payload["type"], "error")
            self.assertIn("já foi iniciada", payload["message"])
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_remover_conexao_limpa_sala(self):
        server = LobbyServer()
        conn_a, conn_b = socket.socketpair()

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 4"})
            self.assertIn(conn_a, server.rooms["Sala 4"])

            server._remove_connection(conn_a)
            self.assertNotIn("Sala 4", server.rooms)
        finally:
            conn_a.close()
            conn_b.close()

    def test_action_emite_snapshot_do_estado_da_sala(self):
        server = LobbyServer()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()
        room_code = f"Sala {uuid4()}"

        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": room_code})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": room_code})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": room_code,
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"}
            })
            receive_message(peer_a)
            receive_message(peer_b)

            server._handle_action(conn_a, {"type": "action", "action": "attack", "target": "Bob"})
            payload = receive_message(peer_a)

            self.assertEqual(payload["type"], "action_ack")
            self.assertEqual(payload["next_turn"], "Bob")
            self.assertEqual(payload["room"], room_code)
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_criar_sala_gera_codigo_de_convite(self):
        server = LobbyServer()
        conn_a, peer_a = socket.socketpair()

        try:
            server._handle_message(conn_a, {"type": "create_room", "player": "Alice"})
            payload = receive_message(peer_a)

            self.assertEqual(payload["type"], "room_created")
            self.assertEqual(payload["player"], "Alice")
            self.assertEqual(len(payload["code"]), 6)
            self.assertIn(payload["code"], server.rooms)
        finally:
            conn_a.close()
            peer_a.close()

    def test_iniciar_partida_cria_estado_de_jogo(self):
        server = LobbyServer()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()

        try:
            server._handle_message(conn_a, {"type": "create_room", "player": "Alice"})
            room_code = receive_message(peer_a)["code"]

            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": room_code})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_a, {
                "type": "start_match",
                "room": room_code,
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"}
            })
            payload = receive_message(peer_a)

            self.assertEqual(payload["type"], "match_started")
            self.assertIn("match", server.room_state[room_code])
            self.assertEqual(len(server.room_state[room_code]["players"]), 2)
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_receive_message_rejeita_tamanho_excessivo(self):
        conn, peer = socket.socketpair()
        try:
            peer.sendall((MAX_MESSAGE + 1).to_bytes(4, byteorder="big"))
            conn.settimeout(0.5)
            self.assertIsNone(receive_message(conn))
        finally:
            conn.close()
            peer.close()

    def test_start_match_rejeita_quem_nao_e_anfitriao(self):
        server = self.make_server()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()
        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala Host"})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala Host"})
            receive_message(peer_b)
            receive_message(peer_a)

            server._handle_message(conn_b, {
                "type": "start_match",
                "room": "Sala Host",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            payload = receive_message(peer_b)
            self.assertEqual(payload["type"], "error")
            self.assertIn("anfitriao", payload["message"])
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

    def test_partida_restaurada_permite_reconectar_jogadores_originais(self):
        server = self.make_server()
        conn_a, peer_a = socket.socketpair()
        conn_b, peer_b = socket.socketpair()
        try:
            server._handle_join(conn_a, {"type": "join", "player": "Alice", "room": "Sala 8"})
            receive_message(peer_a)
            server._handle_join(conn_b, {"type": "join", "player": "Bob", "room": "Sala 8"})
            receive_message(peer_b)
            receive_message(peer_a)
            server._handle_message(conn_a, {
                "type": "start_match",
                "room": "Sala 8",
                "classes": {"Alice": "Guerreiro", "Bob": "Mago"},
            })
            receive_message(peer_a)
            receive_message(peer_b)
            server.save_state()
        finally:
            conn_a.close()
            conn_b.close()
            peer_a.close()
            peer_b.close()

        recovered = LobbyServer(state_path=server.state_path)
        self.assertEqual(recovered.rooms["Sala 8"], [])
        self.assertEqual(recovered.room_state["Sala 8"]["status"], "started")
        self.assertIsNotNone(recovered.room_state["Sala 8"]["match"])

        nova_a, peer_na = socket.socketpair()
        nova_b, peer_nb = socket.socketpair()
        extra, peer_extra = socket.socketpair()
        try:
            peer_na.settimeout(0.5)
            peer_nb.settimeout(0.5)
            peer_extra.settimeout(0.5)
            recovered._handle_join(extra, {"type": "join", "player": "Felix", "room": "Sala 8"})
            tardio = receive_message(peer_extra)
            self.assertEqual(tardio["type"], "error")
            self.assertIn("já foi iniciada", tardio["message"])

            recovered._handle_join(nova_a, {"type": "join", "player": "Alice", "room": "Sala 8"})
            receive_message(peer_na)
            recovered._handle_join(nova_b, {"type": "join", "player": "Bob", "room": "Sala 8"})
            receive_message(peer_nb)
            receive_message(peer_na)
            self.assertEqual(
                [recovered.connections[c]["player"] for c in recovered.room_state["Sala 8"]["order"]],
                ["Alice", "Bob"],
            )
            self.assertEqual(recovered.room_state["Sala 8"]["current_turn"], nova_a)

            recovered._handle_action(nova_a, {"type": "action", "action": "attack", "target": "Bob"})
            ack = receive_message(peer_na)
            self.assertEqual(ack["type"], "action_ack")
            self.assertEqual(ack["next_turn"], "Bob")
        finally:
            nova_a.close()
            nova_b.close()
            extra.close()
            peer_na.close()
            peer_nb.close()
            peer_extra.close()


if __name__ == "__main__":
    unittest.main()
