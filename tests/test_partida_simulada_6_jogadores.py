import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from combate import resolver_ataque
from jogador import Jogador
from partida import Partida
import web.site as site
from web.lobby import Lobby
from web.site import LobbyRequestHandler


class _Nada:
    def start(self):
        return self

    def stop(self):
        return None


def silenciar_sleep():
    return _Nada()


class SequenciaDados:
    def __init__(self, d20s=None, d10s=None):
        self.d20s = list(d20s or [])
        self.d10s = list(d10s or [])

    def d20(self):
        return self.d20s.pop(0) if self.d20s else 18

    def d10(self):
        return self.d10s.pop(0) if self.d10s else 5


def amarrar_dados(jogadores, dados):
    for jogador in jogadores:
        jogador.d20 = dados.d20
        jogador.d10 = dados.d10


NOMES = ["Ana", "Bruno", "Carla", "Diego", "Eva", "Fabio"]


class TestPartidaSimulada6Jogadores(unittest.TestCase):
    def setUp(self):
        self.sleep = silenciar_sleep()
        self.sleep.start()
        self.jogadores = Jogador.criar_elenco(NOMES)
        self.partida = Partida(self.jogadores)
        self.log = []

    def tearDown(self):
        self.sleep.stop()

    def registrar(self, mensagem):
        self.log.append(mensagem)

    def test_partida_completa_com_seis_jogadores(self):
        ana, bruno, carla, diego, eva, fabio = self.jogadores
        partida = self.partida

        self.assertEqual(
            [jogador.passiva for jogador in self.jogadores],
            ["Bruto", "Arcano", "Preciso", "Bruto", "Arcano", "Preciso"],
        )
        self.assertEqual(len(partida.vivos()), 6)
        self.assertEqual(partida.proximo_vivo(ana), bruno)
        self.registrar("Partida iniciada com 6 jogadores.")

        dados = SequenciaDados(d20s=[1])
        amarrar_dados(self.jogadores, dados)
        hp_bruno = bruno.hp
        resultado = resolver_ataque(ana, bruno)
        self.assertFalse(resultado["acertou"])
        self.assertEqual(bruno.hp, hp_bruno)
        self.registrar("Ana errou o ataque em Bruno.")

        hp_ana = ana.hp
        self.assertTrue(bruno.usar_magia("Bola de Fogo", ana))
        self.assertEqual(bruno.mana, 5)
        self.assertEqual(ana.hp, hp_ana - 19)
        self.registrar("Bruno lancou Bola de Fogo em Ana.")

        dados = SequenciaDados(d20s=[18], d10s=[6])
        amarrar_dados([carla], dados)
        hp_diego = diego.hp
        resultado = resolver_ataque(carla, diego)
        self.assertTrue(resultado["acertou"])
        self.assertEqual(diego.hp, hp_diego - resultado["dano"])
        self.registrar(f"Carla atacou Diego e causou {resultado['dano']} de dano.")

        ana.hp = 40
        self.assertTrue(diego.usar_magia("Cura Leve", ana))
        self.assertEqual(ana.hp, 57)
        self.assertEqual(diego.mana, 2)
        self.registrar("Diego curou Ana.")

        hp_fabio = fabio.hp
        self.assertTrue(eva.usar_magia("Bola de Fogo", fabio))
        self.assertEqual(fabio.hp, hp_fabio - 20)
        self.assertEqual(eva.mana, 5)
        self.registrar("Eva lancou Bola de Fogo em Fabio.")

        dados = SequenciaDados(d20s=[18], d10s=[5])
        amarrar_dados([fabio], dados)
        hp_eva = eva.hp
        resultado = resolver_ataque(fabio, eva)
        self.assertTrue(resultado["acertou"])
        self.assertEqual(eva.hp, hp_eva - resultado["dano"])
        self.registrar(f"Fabio atacou Eva e causou {resultado['dano']} de dano.")

        bruno.hp = 0
        carla.hp = 0
        diego.hp = 0
        eva.hp = 0
        fabio.hp = 0
        partida.verificar_mortos()
        self.assertTrue(partida.fim_partida())
        self.assertEqual(partida.vivos()[0].nome, "Ana")
        self.assertEqual(len(partida.mortos), 5)
        self.registrar("Ana venceu a partida de 6 jogadores.")

        print("\n=== LOG DA PARTIDA DE 6 JOGADORES ===")
        for linha in self.log:
            print(f"- {linha}")

    def test_lobby_cria_uma_sala_e_joga_com_seis(self):
        lobby = Lobby()
        sala = lobby.create_room("Ana")
        codigo = sala["code"]

        for _ in range(7):
            repetida = lobby.create_room("Ana")
            self.assertEqual(repetida["code"], codigo)
        self.assertEqual(len(lobby.list_rooms()["rooms"]), 1)

        for nome in ["Bruno", "Carla", "Diego", "Eva", "Fabio"]:
            lobby.join_room(nome, codigo)

        with self.assertRaisesRegex(ValueError, "cheia"):
            lobby.join_room("Gabi", codigo)
        self.assertEqual(len(lobby.get_room(codigo)["room"]["players"]), 6)

        ainda_unica = lobby.create_room("Ana")
        self.assertEqual(ainda_unica["code"], codigo)
        self.assertEqual(len(lobby.list_rooms()["rooms"]), 1)

        lobby.start_match(codigo, token=lobby.token_of(codigo, "Ana"))
        estado = lobby.get_room(codigo)["room"]
        self.assertEqual(estado["status"], "started")
        self.assertEqual(estado["current_turn"], "Ana")
        self.assertEqual(len(estado["players"]), 6)

        match = lobby.rooms[codigo]["match"]
        dados = SequenciaDados()
        amarrar_dados(match.jogadores, dados)

        resultado = lobby.perform_action(codigo, "Ana", "attack", "Bruno", token=lobby.token_of(codigo, "Ana"))
        self.assertEqual(resultado["next_turn"], "Bruno")

        resultado = lobby.perform_action(codigo, "Bruno", "use_magic", target="Ana", magic="Bola de Fogo", token=lobby.token_of(codigo, "Bruno"))
        self.assertEqual(resultado["type"], "magic")
        self.assertEqual(resultado["next_turn"], "Carla")

        resultado = lobby.perform_action(codigo, "Carla", "attack", "Diego", token=lobby.token_of(codigo, "Carla"))
        if resultado.get("extra"):
            resultado = lobby.perform_action(codigo, "Carla", "attack", "Diego", token=lobby.token_of(codigo, "Carla"))
        self.assertEqual(resultado["next_turn"], "Diego")

        resultado = lobby.perform_action(codigo, "Diego", "use_magic", target="Ana", magic="Cura Leve", token=lobby.token_of(codigo, "Diego"))
        self.assertEqual(resultado["type"], "magic")
        self.assertFalse(resultado.get("extra"))
        self.assertEqual(resultado["next_turn"], "Eva")

        resultado = lobby.perform_action(codigo, "Eva", "use_magic", target="Fabio", magic="Bola de Fogo", token=lobby.token_of(codigo, "Eva"))
        self.assertEqual(resultado["type"], "magic")
        self.assertEqual(resultado["next_turn"], "Fabio")

        resultado = lobby.perform_action(codigo, "Fabio", "attack", "Eva", token=lobby.token_of(codigo, "Fabio"))
        self.assertEqual(resultado["next_turn"], "Ana")

        for jogador in match.jogadores:
            if jogador.nome not in {"Ana", "Bruno"}:
                jogador.hp = 0
        next(jogador for jogador in match.jogadores if jogador.nome == "Bruno").hp = 1

        resultado = lobby.perform_action(codigo, "Ana", "attack", "Bruno", token=lobby.token_of(codigo, "Ana"))
        self.assertEqual(resultado["status"], "finished")
        self.assertEqual(resultado["winner"], "Ana")
        self.assertEqual(lobby.list_rooms()["rooms"], [])


class TestHttpNaoCriaSalaInfinita(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_lobby = site.lobby
        site.lobby = Lobby()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LobbyRequestHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        site.lobby = cls._original_lobby

    def _post(self, path, payload):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def _get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_oito_creates_do_mesmo_host_viram_uma_sala_de_seis(self):
        codigos = []
        for _ in range(8):
            status, created = self._post("/api/create-room", {"player": "Ana6"})
            self.assertEqual(status, 200)
            codigos.append(created["code"])
        self.assertEqual(len(set(codigos)), 1)
        codigo = codigos[0]

        for nome in ["Bruno6", "Carla6", "Diego6", "Eva6", "Fabio6"]:
            status, joined = self._post("/api/join-room", {"player": nome, "room": codigo})
            self.assertEqual(status, 200)
            self.assertEqual(joined["code"], codigo)

        with self.assertRaises(urllib.error.HTTPError) as contexto:
            self._post("/api/join-room", {"player": "Gabi6", "room": codigo})
        self.assertEqual(contexto.exception.code, 400)
        erro = json.loads(contexto.exception.read().decode("utf-8"))
        self.assertIn("cheia", erro["error"])

        status, rooms = self._get("/api/rooms")
        self.assertEqual(status, 200)
        desta = [sala for sala in rooms["rooms"] if sala["code"] == codigo]
        self.assertEqual(len(desta), 1)
        self.assertEqual(len(desta[0]["players"]), 6)

        status, started = self._post("/api/start-match", {"room": codigo, "token": created["token"]})
        self.assertEqual(status, 200)
        self.assertEqual(started["status"], "started")
        self.assertEqual(len(started["players"]), 6)
        self.assertEqual(started["current_turn"], "Ana6")


if __name__ == "__main__":
    unittest.main(verbosity=2)
