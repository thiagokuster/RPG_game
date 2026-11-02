import unittest
from unittest.mock import patch

from combate import resolver_ataque
from jogador import Jogador


class TestIdentidadeClasses(unittest.TestCase):
    def setUp(self):
        self.sleep = patch("jogador.jogador.sleep", lambda *_a, **_k: None)
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()

    def test_kits_iniciais(self):
        guerreiro = Jogador.criar_por_classe("Ana", "Guerreiro")
        mago = Jogador.criar_por_classe("Bruno", "Mago")
        arqueiro = Jogador.criar_por_classe("Carla", "Arqueiro")

        self.assertEqual(guerreiro.arma.nome, "Espada de Treino")
        self.assertEqual(mago.anel.nome, "Anel Arcano")
        self.assertEqual(mago.max_mana, 7)
        self.assertEqual(arqueiro.anel.nome, "Anel da Sorte")
        self.assertEqual(arqueiro.sorte, 3)

    def test_guerreiro_reduz_dano_e_critica_em_19(self):
        ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        bruno.d20 = lambda: 18
        bruno.d10 = lambda: 5
        hp = ana.hp
        resultado = resolver_ataque(bruno, ana)
        self.assertTrue(resultado["acertou"])
        self.assertEqual(resultado["reduzido"], 1)
        self.assertEqual(ana.hp, hp - resultado["dano"])

        ana.d20 = lambda: 19
        ana.d10 = lambda: 5
        hp_bruno = bruno.hp
        critico = resolver_ataque(ana, bruno)
        self.assertTrue(critico["critico"])
        self.assertEqual(bruno.hp, hp_bruno - critico["dano"])

    def test_paladino_cura_metade_e_pode_agir_de_novo(self):
        diego = Jogador.criar_por_classe("Diego", "Paladino")
        diego.hp = 40
        diego.iniciar_turno()
        self.assertTrue(diego.usar_magia("Cura Leve", diego))
        self.assertEqual(diego.hp, 48)
        self.assertFalse(diego.gasta_turno)

    def test_clerigo_nao_gasta_turno_em_alvo_ferido(self):
        eva = Jogador.criar_por_classe("Eva", "Clerigo")
        alvo = Jogador.criar_por_classe("Ana", "Guerreiro")
        alvo.hp = 80
        eva.iniciar_turno()
        self.assertTrue(eva.usar_magia("Rajada Congelante", alvo))
        self.assertFalse(eva.gasta_turno)

    def test_mago_recupera_mana_na_rodada(self):
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        bruno.mana = 3
        bruno.inicio_rodada()
        self.assertEqual(bruno.mana, 4)


if __name__ == "__main__":
    unittest.main()
