import unittest
from unittest.mock import patch

from jogador import Jogador
from monstro import Monstro
from partida import Partida
from web.lobby import Lobby


class TestChefe(unittest.TestCase):
    def test_escolhe_o_mais_ferido_na_maioria_das_vezes(self):
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        ana.hp = 20
        bruno.hp = 80
        with patch("monstro.monstro.randint", return_value=1):
            self.assertEqual(Monstro.escolher_alvo([ana, bruno]).nome, "Ana")
        with patch("monstro.monstro.randint", return_value=10), patch("monstro.monstro.choice", return_value=bruno):
            self.assertEqual(Monstro.escolher_alvo([ana, bruno]).nome, "Bruno")

    def test_pisada_atinge_os_dois_mais_feridos(self):
        chefe = Monstro.gerar_chefe(1)
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        carla = Jogador.criar("Carla", passiva="Preciso")
        ana.hp = 10
        bruno.hp = 20
        carla.hp = 90
        resultado = chefe.pisada([ana, bruno, carla])
        alvos = [ev.get("para") for ev in resultado["eventos"] if ev.get("tipo") == "magia"]
        self.assertEqual(set(alvos), {"Ana", "Bruno"})
        self.assertLess(ana.hp, 10)
        self.assertLess(bruno.hp, 20)
        self.assertEqual(carla.hp, 90)

    def test_agir_usa_pisada_a_cada_tres_turnos(self):
        chefe = Monstro.gerar_chefe(2)
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        chefe.turnos = 2
        with patch.object(chefe, "pisada", wraps=chefe.pisada) as pisada:
            chefe.agir([ana, bruno])
            pisada.assert_called_once()

    def test_coop_avanca_ondas_ate_tres(self):
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        chefe = Monstro.gerar_chefe(1)
        partida = Partida([ana, bruno, chefe], modo="coop")
        self.assertEqual(partida.onda, 1)
        chefe.hp = 0
        partida.verificar_mortos()
        eventos = partida.tentar_proxima_onda()
        self.assertEqual(partida.onda, 2)
        self.assertEqual(eventos[0]["tipo"], "onda")
        self.assertFalse(partida.fim_partida())
        partida.jogadores[-1].hp = 0
        partida.verificar_mortos()
        partida.tentar_proxima_onda()
        self.assertEqual(partida.onda, 3)
        partida.jogadores[-1].hp = 0
        partida.verificar_mortos()
        self.assertEqual(partida.tentar_proxima_onda(), [])
        self.assertTrue(partida.fim_partida())

    def test_lobby_coop_chefe_nao_fica_so_no_primeiro(self):
        lobby = Lobby()
        sala = lobby.create_room("Ana")
        lobby.join_room("Bruno", sala["code"])
        started = lobby.start_match(
            sala["code"],
            {"Ana": "Bruto", "Bruno": "Arcano"},
            token=lobby.token_of(sala["code"], "Ana"),
            modo="coop",
        )
        self.assertEqual(started["modo"], "coop")
        match = lobby.rooms[sala["code"]]["match"]
        ana = next(j for j in match.jogadores if j.nome == "Ana")
        bruno = next(j for j in match.jogadores if j.nome == "Bruno")
        chefe = next(j for j in match.jogadores if getattr(j, "tipo", "") == "chefe")
        ana.hp = 8
        bruno.hp = 80
        with patch("monstro.monstro.randint", return_value=1):
            alvo = chefe.escolher_alvo([ana, bruno])
        self.assertEqual(alvo.nome, "Ana")


if __name__ == "__main__":
    unittest.main()
