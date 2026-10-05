import unittest

from combate.combate import Combate
from jogador.jogador import Jogador


class TestCombate(unittest.TestCase):
    def test_atacar_retorna_false_quando_erra(self):
        atacante = Jogador("Atacante", 100)
        alvo = Jogador("Alvo", 100)
        alvo.armor_class = 18
        combate = Combate(atacante, [atacante, alvo], 0)
        combate.alvo = alvo

        atacante.d20 = lambda: 1
        atacante.d10 = lambda: 5
        atacante.ataque_bonus = 2
        atacante.proficiencia = 2

        self.assertFalse(combate.atacar())

    def test_atacar_retorna_true_quando_acerta(self):
        atacante = Jogador("Atacante", 100)
        alvo = Jogador("Alvo", 100)
        alvo.armor_class = 12
        combate = Combate(atacante, [atacante, alvo], 0)
        combate.alvo = alvo

        atacante.d20 = lambda: 20
        atacante.d10 = lambda: 5
        atacante.ataque_bonus = 2
        atacante.proficiencia = 2

        self.assertTrue(combate.atacar())


if __name__ == "__main__":
    unittest.main()
