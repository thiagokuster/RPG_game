import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from online.client import GameClient
from online.server import LobbyServer


class TestOnlineE2E(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.clients = []
        self.ready = threading.Event()
        self.server = LobbyServer(
            host="127.0.0.1",
            port=0,
            state_path=Path(self.temp_dir.name) / "rooms.json",
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"ready": self.ready},
            daemon=True,
        )
        self.thread.start()
        self.assertTrue(self.ready.wait(timeout=3), "Servidor online nao subiu a tempo.")
        self.host = "127.0.0.1"
        self.port = self.server.port
        self.sleep_patch = patch("jogador.jogador.sleep", lambda *_a, **_k: None)
        self.sleep_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()
        for client in self.clients:
            client.close()

    def conectar(self, player, room="Arena", join=True):
        client = GameClient(host=self.host, port=self.port, player=player, room=room)
        for _ in range(20):
            try:
                client.connect(join=join)
                break
            except OSError:
                time.sleep(0.05)
        else:
            client.connect(join=join)
        self.clients.append(client)
        return client

    def drenar(self, client, limite=8):
        mensagens = []
        for _ in range(limite):
            mensagem = client.receive(timeout=0.2)
            if mensagem is None:
                break
            mensagens.append(mensagem)
        return mensagens

    def receber_tipo(self, client, tipo, tentativas=8):
        for _ in range(tentativas):
            mensagem = client.receive(timeout=2)
            self.assertIsNotNone(mensagem, f"Sem mensagem {tipo} de {client.player}")
            if mensagem.get("type") == tipo:
                return mensagem
        self.fail(f"{client.player} nao recebeu mensagem do tipo {tipo}")

    def test_partida_tcp_com_dois_clientes(self):
        ana = self.conectar("Ana")
        bruno = self.conectar("Bruno")
        joined = self.receber_tipo(ana, "player_joined")
        self.assertIn("Bruno", joined["players"])

        ana.list_rooms()
        salas = self.receber_tipo(ana, "rooms")
        self.assertIn("Arena", salas["rooms"])
        self.assertCountEqual(salas["rooms"]["Arena"], ["Ana", "Bruno"])

        duplicado = GameClient(host=self.host, port=self.port, player="Ana", room="Arena")
        erro_nome = duplicado.connect()
        self.clients.append(duplicado)
        self.assertEqual(erro_nome["type"], "error")
        self.assertIn("já existe", erro_nome["message"])

        ana.start_match({"Ana": "Guerreiro", "Bruno": "Mago"})
        inicio_ana = self.receber_tipo(ana, "match_started")
        inicio_bruno = self.receber_tipo(bruno, "match_started")
        self.assertEqual(inicio_ana["status"], "started")
        self.assertEqual(inicio_bruno["current_turn"], "Ana")
        self.assertEqual(len(inicio_ana["match"]["players"]), 2)

        with patch("jogador.Jogador.d20", return_value=1):
            ana.send_action("attack", target="Bruno")
            ack = self.receber_tipo(ana, "action_ack")
            evento = self.receber_tipo(bruno, "action")
        self.assertEqual(ack["next_turn"], "Bruno")
        self.assertEqual(evento["result"], "miss")
        self.assertEqual(evento["player"], "Ana")

        ana.send_action("attack", target="Bruno")
        fora_da_vez = self.receber_tipo(ana, "error")
        self.assertEqual(fora_da_vez["message"], "Nao e sua vez.")

        bruno.send_action("use_magic", magic="Bola de Fogo", target="Ana")
        magia = self.receber_tipo(bruno, "magic")
        self.assertEqual(magia["magic"], "Bola de Fogo")
        self.assertEqual(magia["next_turn"], "Ana")
        self.drenar(ana)

        tardio = GameClient(host=self.host, port=self.port, player="Carla", room="Arena")
        erro_tardio = tardio.connect()
        self.clients.append(tardio)
        self.assertEqual(erro_tardio["type"], "error")
        self.assertIn("já foi iniciada", erro_tardio["message"])

    def test_criar_sala_e_convidar_pelo_codigo(self):
        ana = self.conectar("Ana", join=False)
        criada = ana.create_room()
        self.assertEqual(criada["type"], "room_created")
        self.assertEqual(len(criada["code"]), 6)

        bruno = self.conectar("Bruno", room=criada["code"])
        convite = self.receber_tipo(ana, "player_joined")
        self.assertIn("Bruno", convite["players"])

        ana.start_match({"Ana": "Arqueiro", "Bruno": "Clerigo"})
        inicio = self.receber_tipo(ana, "match_started")
        self.receber_tipo(bruno, "match_started")
        self.assertEqual(inicio["match"]["players"][0]["classe"], "Arqueiro")
        self.assertEqual(inicio["match"]["players"][1]["classe"], "Clerigo")

    def test_parse_comandos_de_sala(self):
        self.assertEqual(
            GameClient.parse_command("start Ana:Guerreiro Bruno:Mago"),
            {"action": "start_match", "classes": {"Ana": "Guerreiro", "Bruno": "Mago"}},
        )
        self.assertEqual(GameClient.parse_command("list"), {"action": "list_rooms"})
        self.assertEqual(GameClient.parse_command("create"), {"action": "create_room"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
