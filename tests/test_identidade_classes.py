import unittest

from combate import resolver_ataque
from jogador import Jogador


class TestAventureiro(unittest.TestCase):
    def test_todos_nascem_iguais(self):
        ana = Jogador.criar("Ana")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        carla = Jogador.criar("Carla")

        for jogador in (ana, bruno, carla):
            self.assertEqual(jogador.classe, "Aventureiro")
            self.assertEqual(jogador.max_hp, 100)
            self.assertEqual(jogador.armor_class, 14)
            self.assertEqual(jogador.max_mana, 4)
            self.assertEqual(jogador.sorte, 2)
            self.assertEqual(jogador.reducao_nativa, 0)
            self.assertEqual(jogador.critico, 20)
            self.assertFalse(jogador.tiro_multiplo)
            self.assertEqual(jogador.arma.nome, "Espada de Treino")
            self.assertEqual(
                [magia.nome for magia in jogador.magias],
                ["Bola de Fogo", "Cura Leve", "Rajada Congelante"],
            )

    def test_critico_so_no_20_sem_reducao_nativa(self):
        ana = Jogador.criar("Ana")
        bruno = Jogador.criar("Bruno")
        bruno.d20 = lambda: 18
        bruno.d10 = lambda: 5
        hp = ana.hp
        resultado = resolver_ataque(bruno, ana)
        self.assertTrue(resultado["acertou"])
        self.assertEqual(resultado["reduzido"], 0)
        self.assertEqual(ana.hp, hp - resultado["dano"])

        ana.d20 = lambda: 19
        ana.d10 = lambda: 5
        falha = resolver_ataque(ana, bruno)
        self.assertFalse(falha["critico"])

        ana.d20 = lambda: 20
        critico = resolver_ataque(ana, bruno)
        self.assertTrue(critico["critico"])
        self.assertEqual(critico["dano"], 38)

    def test_cura_e_rajada_gastam_o_turno(self):
        diego = Jogador.criar("Diego")
        diego.hp = 40
        diego.iniciar_turno()
        self.assertTrue(diego.usar_magia("Cura Leve", diego))
        self.assertEqual(diego.hp, 57)
        self.assertTrue(diego.gasta_turno)

        eva = Jogador.criar("Eva")
        alvo = Jogador.criar("Ana")
        alvo.hp = 80
        eva.iniciar_turno()
        self.assertTrue(eva.usar_magia("Rajada Congelante", alvo))
        self.assertTrue(eva.gasta_turno)

    def test_nao_tem_folego_nem_mana_por_rodada(self):
        ana = Jogador.criar("Ana")
        self.assertFalse(ana.usar_magia("Segundo Folego", ana))

        bruno = Jogador.criar("Bruno")
        bruno.mana = 3
        bruno.inicio_rodada()
        self.assertEqual(bruno.mana, 3)


if __name__ == "__main__":
    unittest.main()
