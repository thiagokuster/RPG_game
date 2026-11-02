import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from combate import Combate, resolver_ataque
from equipamento import Equipamento
from jogador import Jogador
from loja import Loja
from monstro import Monstro
from online.client import GameClient
from online.server import LobbyServer
from partida import Partida
from private.lobby import PrivateLobby


def silenciar_sleep():
    return patch.multiple(
        "jogador.jogador",
        sleep=lambda *_a, **_k: None,
    )


class SequenciaDados:
    def __init__(self, d20s=None, d10s=None):
        self.d20s = list(d20s or [])
        self.d10s = list(d10s or [])

    def d20(self):
        return self.d20s.pop(0) if self.d20s else 11

    def d10(self):
        return self.d10s.pop(0) if self.d10s else 5


def amarrar_dados(jogadores, dados):
    for jogador in jogadores:
        jogador.d20 = dados.d20
        jogador.d10 = dados.d10


class TestPartidaSimulada5Jogadores(unittest.TestCase):
    def setUp(self):
        self.sleep = silenciar_sleep()
        self.sleep.start()
        self.ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        self.bruno = Jogador.criar_por_classe("Bruno", "Mago")
        self.carla = Jogador.criar_por_classe("Carla", "Arqueiro")
        self.diego = Jogador.criar_por_classe("Diego", "Paladino")
        self.eva = Jogador.criar_por_classe("Eva", "Clerigo")
        self.jogadores = [self.ana, self.bruno, self.carla, self.diego, self.eva]
        self.partida = Partida(self.jogadores)
        self.loja = Loja()
        self.log = []

    def tearDown(self):
        self.sleep.stop()

    def registrar(self, mensagem):
        self.log.append(mensagem)

    def test_partida_completa_com_cinco_classes_e_todas_as_acoes(self):
        ana, bruno, carla, diego, eva = self.jogadores
        partida = self.partida

        self.assertEqual([j.classe for j in self.jogadores], ["Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo"])
        self.assertEqual(ana.max_mana, 0)
        self.assertEqual(bruno.max_mana, 7)
        self.assertEqual(diego.max_mana, 4)
        self.assertEqual(eva.max_mana, 5)
        self.assertEqual(len(self.loja.estoque), 3)
        self.assertEqual(partida.proximo_vivo(ana), bruno)
        self.registrar("Partida iniciada com 5 jogadores. Loja ja tem estoque.")

        dados = SequenciaDados(d20s=[1], d10s=[5])
        amarrar_dados(self.jogadores, dados)
        hp_bruno = bruno.hp
        resultado = resolver_ataque(ana, bruno)
        self.assertFalse(resultado["acertou"])
        self.assertEqual(bruno.hp, hp_bruno)
        self.assertEqual(partida.proximo_vivo(ana), bruno)
        self.registrar("Ana errou o ataque em Bruno. Turno segue para Bruno.")

        hp_ana = ana.hp
        self.assertTrue(bruno.usar_magia("Bola de Fogo", ana))
        self.assertEqual(bruno.mana, 5)
        self.assertEqual(ana.hp, hp_ana - 19)
        self.assertEqual(partida.proximo_vivo(bruno), carla)
        self.registrar("Bruno lancou Bola de Fogo em Ana (20 dano, 2 mana).")

        carla.moedas = 30
        arma1 = Equipamento("Espada Curta", dano=4, valor=4, tipo="arma", bonus_ataque=2)
        arma2 = Equipamento("Machado", dano=6, valor=6, tipo="arma", bonus_ataque=2)
        anel = Equipamento("Amuleto do Valor", valor=4, tipo="anel", agilidade=1)
        armadura = Equipamento("Peitoral", valor=6, tipo="armadura", armadura=3)
        self.loja.estoque = [arma1, arma2, anel, armadura]
        self.assertTrue(self.loja.tem_moeda(carla, arma1.valor))
        carla.adicionar_item_inventario(arma1)
        self.loja.estoque.remove(arma1)
        self.assertTrue(self.loja.tem_moeda(carla, arma2.valor))
        carla.adicionar_item_inventario(arma2)
        self.loja.estoque.remove(arma2)
        self.assertTrue(self.loja.tem_moeda(carla, anel.valor))
        carla.adicionar_item_inventario(anel)
        self.loja.estoque.remove(anel)
        self.assertTrue(self.loja.tem_moeda(carla, armadura.valor))
        carla.adicionar_item_inventario(armadura)
        self.loja.estoque.remove(armadura)

        base_ataque = carla.ataque_bonus
        base_ca = carla.armor_class
        carla.equipar(arma1)
        self.assertEqual(carla.ataque_bonus, base_ataque + 2)
        carla.equipar(arma2)
        self.assertEqual(carla.ataque_bonus, base_ataque + 2)
        self.assertEqual(carla.arma.nome, "Machado")
        carla.equipar(arma2)
        self.assertEqual(carla.ataque_bonus, base_ataque + 2)
        carla.equipar(armadura)
        self.assertEqual(carla.armor_class, base_ca + 3)
        carla.equipar(anel)
        self.assertEqual(carla.agilidadebase, 1)
        self.assertEqual(carla.armor_class, base_ca + 3 + 1)
        self.assertEqual(carla.bonus_ataque_total, carla.ataque_bonus + carla.proficiencia + 1 + carla.bonus_acerto)
        self.registrar("Carla comprou e trocou equipamentos sem empilhar bonus.")

        ana.hp = 40
        hp_diego = diego.hp
        self.assertTrue(diego.usar_magia("Cura Leve", ana))
        self.assertEqual(ana.hp, 48)
        self.assertEqual(diego.hp, hp_diego)
        self.assertEqual(diego.mana, 3)
        self.registrar("Diego curou Ana, nao a si mesmo.")

        hp_bruno = bruno.hp
        self.assertTrue(eva.usar_magia("Rajada Congelante", bruno))
        self.assertEqual(bruno.hp, hp_bruno - 14)
        self.assertEqual(eva.mana, 3)
        self.registrar("Eva acertou Rajada Congelante em Bruno.")

        dados = SequenciaDados(d20s=[20], d10s=[5])
        amarrar_dados([ana], dados)
        hp_bruno = bruno.hp
        resultado = resolver_ataque(ana, bruno)
        self.assertTrue(resultado["acertou"])
        self.assertTrue(resultado["critico"])
        self.assertEqual(resultado["dano"], 38)
        self.assertEqual(bruno.hp, hp_bruno - 38)
        self.registrar("Ana cravou critico 2x (38), nao 4x.")

        bruno.hp = 1
        dados = SequenciaDados(d20s=[18], d10s=[6])
        amarrar_dados([ana], dados)
        resolver_ataque(ana, bruno)
        partida.verificar_mortos()
        self.assertIn(bruno, partida.mortos)
        self.assertEqual(len(partida.vivos()), 4)
        self.assertEqual(partida.proximo_vivo(ana), carla)
        self.assertNotEqual(partida.proximo_vivo(ana), bruno)
        self.registrar("Bruno morreu. Turno pula o morto e vai para Carla.")

        self.assertFalse(bruno.usar_magia("Bola de Fogo", ana))
        eva.mana = 0
        self.assertFalse(eva.usar_magia("Cura Leve", ana))
        self.registrar("Magia sem mana ou de jogador morto foi recusada.")

        monstro = Monstro("Goblin", hp=8, ataque_bonus=1, armor_class=5, dano=2, xp=20, recompensa=12)
        dados = SequenciaDados(d20s=[18], d10s=[4])
        amarrar_dados([carla], dados)
        with patch.object(monstro, "atacar", return_value=0):
            venceu = partida.resolver_evento_monstro(carla, monstro)
        self.assertTrue(venceu)
        self.assertEqual(monstro.hp, 0)
        self.assertGreaterEqual(carla.moedas, 12)
        self.registrar("Carla venceu o evento de monstro com a mesma formula de combate.")

        combate = Combate(ana, self.jogadores, 0)
        alvos = [jogador.nome for _, jogador in combate.alvos_disponiveis()]
        self.assertNotIn("Ana", alvos)
        self.assertNotIn("Bruno", alvos)
        self.assertEqual(set(alvos), {"Carla", "Diego", "Eva"})

        diego.hp = 0
        eva.hp = 0
        carla.hp = 0
        partida.verificar_mortos()
        self.assertTrue(partida.fim_partida())
        self.assertEqual(partida.vivos()[0].nome, "Ana")
        self.registrar("Ana venceu a partida de 5 jogadores.")

        print("\n=== LOG DA PARTIDA SIMULADA ===")
        for linha in self.log:
            print(f"- {linha}")

    def test_lobby_web_com_cinco_jogadores(self):
        lobby = PrivateLobby()
        sala = lobby.create_room("Ana")
        codigo = sala["code"]
        for nome in ["Bruno", "Carla", "Diego", "Eva"]:
            lobby.join_room(nome, codigo)

        with self.assertRaisesRegex(ValueError, "já existe"):
            lobby.join_room("Ana", codigo)

        classes = {
            "Ana": "Guerreiro",
            "Bruno": "Mago",
            "Carla": "Arqueiro",
            "Diego": "Paladino",
            "Eva": "Clerigo",
        }
        lobby.start_match(codigo, classes, token=lobby.token_of(codigo, "Ana"))
        with self.assertRaisesRegex(ValueError, "já foi iniciada"):
            lobby.join_room("Felix", codigo)

        estado = lobby.get_room(codigo)["room"]
        bruno = next(player for player in estado["players"] if player["name"] == "Bruno")
        self.assertTrue(bruno["magias"])
        self.assertTrue(estado["shop"])

        with patch("jogador.jogador.sleep", lambda *_a, **_k: None):
            with patch.object(lobby.rooms[codigo]["match"].jogadores[0], "d20", return_value=1):
                resultado = lobby.perform_action(codigo, "Ana", "attack", "Bruno", token=lobby.token_of(codigo, "Ana"))
        self.assertEqual(resultado["next_turn"], "Bruno")

        resultado = lobby.perform_action(codigo, "Bruno", "use_magic", target="Ana", magic="Bola de Fogo", token=lobby.token_of(codigo, "Bruno"))
        self.assertEqual(resultado["type"], "magic")
        self.assertEqual(resultado["next_turn"], "Carla")
        self.assertLess(lobby.rooms[codigo]["match"].jogadores[0].hp, 100)

        snapshot = lobby.get_room(codigo)["room"]
        ana = next(player for player in snapshot["players"] if player["name"] == "Ana")
        self.assertLess(ana["hp"], ana["max_hp"])

    def test_servidor_online_rejeita_nome_duplicado_join_tardio_e_acao_pre_start(self):
        from online.protocol import receive_message

        def drenar(peer):
            peer.settimeout(0.05)
            while True:
                mensagem = receive_message(peer)
                if mensagem is None:
                    break

        with tempfile.TemporaryDirectory() as temp:
            server = LobbyServer(state_path=Path(temp) / "rooms.json")
            pares = [socket.socketpair() for _ in range(6)]
            try:
                nomes = ["Ana", "Bruno", "Carla", "Diego", "Eva"]
                for (conn, peer), nome in zip(pares, nomes):
                    peer.settimeout(0.5)
                    server._handle_join(conn, {"type": "join", "player": nome, "room": "Arena"})
                for _, peer in pares[:5]:
                    drenar(peer)

                extra_conn, extra_peer = pares[5]
                extra_peer.settimeout(0.5)
                server._handle_join(extra_conn, {"type": "join", "player": "Ana", "room": "Arena"})
                erro = receive_message(extra_peer)
                self.assertEqual(erro["type"], "error")
                self.assertIn("já existe", erro["message"])

                ana_conn, ana_peer = pares[0]
                ana_peer.settimeout(0.5)
                server._handle_action(ana_conn, {"type": "action", "action": "attack", "target": "Bruno"})
                payload = receive_message(ana_peer)
                self.assertEqual(payload["message"], "A partida ainda nao foi iniciada.")

                classes = dict(zip(nomes, ["Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo"]))
                server._handle_message(ana_conn, {"type": "start_match", "room": "Arena", "classes": classes})
                for _, peer in pares[:5]:
                    drenar(peer)
                extra_peer.settimeout(0.5)
                server._handle_join(extra_conn, {"type": "join", "player": "Felix", "room": "Arena"})
                tardio = receive_message(extra_peer)
                self.assertIn("já foi iniciada", tardio["message"])
                self.assertEqual(len(server.rooms["Arena"]), 5)
            finally:
                for conn, peer in pares:
                    conn.close()
                    peer.close()

    def test_parse_magia_com_nome_composto(self):
        self.assertEqual(
            GameClient.parse_command("use_magic Bola de Fogo Ana"),
            {"action": "use_magic", "magic": "Bola de Fogo", "target": "Ana"},
        )
        self.assertEqual(
            GameClient.parse_command('use_magic "Cura Leve" Bruno'),
            {"action": "use_magic", "magic": "Cura Leve", "target": "Bruno"},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
