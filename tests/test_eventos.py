import unittest
from unittest.mock import patch

from eventos.eventos import resolver_aposta, resolver_risco, resolver_tesouro
from jogador import Jogador
from partida import Partida


class TestEventos(unittest.TestCase):
    def test_tesouro_aumenta_com_sorte(self):
        jogador = Jogador.criar_por_classe("Ana", "Arqueiro")
        resultado = resolver_tesouro(jogador, rodada=4)
        self.assertEqual(resultado["tipo"], "tesouro")
        self.assertEqual(jogador.moedas, resultado["moedas"])
        self.assertGreaterEqual(resultado["moedas"], 2 + 2 + jogador.sorte)

    def test_aposta_ganha_e_perde_com_dados_controlados(self):
        jogador = Jogador.criar_por_classe("Bruno", "Mago")
        jogador.moedas = 10
        with patch("eventos.eventos.randint", return_value=20), patch("eventos.eventos.uniform", return_value=2.0):
            ganhou = resolver_aposta(jogador, rodada=4, aposta=4)
        self.assertEqual(ganhou["resultado"], "ganhou")
        self.assertEqual(jogador.moedas, 14)

        with patch("eventos.eventos.randint", return_value=1), patch("eventos.eventos.uniform", return_value=1.5):
            perdeu = resolver_aposta(jogador, rodada=4, aposta=4)
        self.assertEqual(perdeu["resultado"], "perdeu")
        self.assertEqual(jogador.moedas, 10)

    def test_risco_respeita_salvamento_de_sorte(self):
        jogador = Jogador.criar_por_classe("Carla", "Arqueiro")
        jogador.moedas = 6
        with patch("eventos.eventos.randint", return_value=20):
            evitou = resolver_risco(jogador, rodada=6)
        self.assertEqual(evitou["resultado"], "evitou")
        self.assertEqual(jogador.moedas, 6)

        with patch("eventos.eventos.randint", return_value=1):
            perdeu = resolver_risco(jogador, rodada=6)
        self.assertEqual(perdeu["resultado"], "perdeu")
        self.assertLess(jogador.moedas, 6)

    def test_partida_resolve_evento_nao_monstro(self):
        jogador = Jogador.criar_por_classe("Diego", "Paladino")
        partida = Partida([jogador])
        resultado = partida.resolver_evento_aleatorio(jogador, {"tipo": "tesouro"}, rodada=2)
        self.assertEqual(resultado["tipo"], "tesouro")
        self.assertGreater(jogador.moedas, 0)


if __name__ == "__main__":
    unittest.main()
