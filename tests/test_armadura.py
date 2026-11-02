import unittest
from unittest.mock import patch

from combate import resolver_ataque
from equipamento import Equipamento
from jogador import Jogador


class TestArmadura(unittest.TestCase):
    def setUp(self):
        self.sleep = patch("jogador.jogador.sleep", lambda *_a, **_k: None)
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()

    def test_armadura_reduz_dano_e_perde_durabilidade(self):
        ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        peca = Equipamento("Couraça", tipo="armadura", armadura=2, reducao=5, durabilidade=8)
        bruno.adicionar_item_inventario(peca)
        bruno.equipar(peca)
        self.assertEqual(bruno.armor_class, 16)

        ana.d20 = lambda: 18
        ana.d10 = lambda: 5
        hp_antes = bruno.hp
        resultado = resolver_ataque(ana, bruno)

        self.assertTrue(resultado["acertou"])
        self.assertEqual(resultado["reduzido"], 5)
        self.assertEqual(resultado["dano"], resultado.get("dano"))
        self.assertEqual(bruno.hp, hp_antes - resultado["dano"])
        self.assertEqual(bruno.armadura.durabilidade, 3)

    def test_armadura_quebra_e_sai_do_inventario(self):
        ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        peca = Equipamento("Gibão", tipo="armadura", armadura=1, reducao=20, durabilidade=2)
        bruno.adicionar_item_inventario(peca)
        bruno.equipar(peca)
        ca_base = 14

        ana.d20 = lambda: 18
        ana.d10 = lambda: 5
        resultado = resolver_ataque(ana, bruno)

        self.assertTrue(resultado["armadura_quebra"])
        self.assertIsNone(bruno.armadura)
        self.assertNotIn(peca, bruno.inventario)
        self.assertEqual(bruno.armor_class, ca_base)

    def test_ataque_sem_armadura_mantem_dano_cheio(self):
        ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        ana.d20 = lambda: 20
        ana.d10 = lambda: 5
        hp_antes = bruno.hp
        resultado = resolver_ataque(ana, bruno)
        self.assertEqual(resultado["dano"], 38)
        self.assertEqual(bruno.hp, hp_antes - 38)


if __name__ == "__main__":
    unittest.main()
