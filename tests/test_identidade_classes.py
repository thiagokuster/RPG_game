import unittest

from combate import resolver_ataque
from jogador import Jogador


class TestPassivas(unittest.TestCase):
    def test_passivas_diferenciam_sem_classe(self):
        bruto = Jogador.criar("Ana", passiva="Bruto")
        arcano = Jogador.criar("Bruno", passiva="Arcano")
        preciso = Jogador.criar("Carla", passiva="Preciso")

        self.assertEqual(bruto.classe, "Aventureiro")
        self.assertEqual(arcano.passiva, "Arcano")
        self.assertEqual(bruto.max_hp, 115)
        self.assertEqual(bruto.reducao_nativa, 1)
        self.assertEqual([m.nome for m in bruto.magias], ["Cura Leve", "Golpe de Energia"])
        self.assertEqual(arcano.max_hp, 90)
        self.assertEqual(arcano.mana_por_rodada, 1)
        self.assertEqual([m.nome for m in arcano.magias], ["Cura Leve", "Bola de Fogo"])
        self.assertEqual(preciso.critico, 19)
        self.assertEqual(preciso.bonus_acerto, 1)
        self.assertEqual([m.nome for m in preciso.magias], ["Cura Leve", "Rajada Congelante"])

    def test_criar_por_classe_vira_passiva(self):
        ana = Jogador.criar_por_classe("Ana", "Guerreiro")
        bruno = Jogador.criar_por_classe("Bruno", "Mago")
        self.assertEqual(ana.passiva, "Bruto")
        self.assertEqual(bruno.passiva, "Arcano")

    def test_bruto_reduz_dano_e_preciso_critica_em_19(self):
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        bruno.d20 = lambda: 18
        bruno.d10 = lambda: 5
        hp = ana.hp
        resultado = resolver_ataque(bruno, ana)
        self.assertTrue(resultado["acertou"])
        self.assertEqual(resultado["reduzido"], 1)
        self.assertEqual(ana.hp, hp - resultado["dano"])

        preciso = Jogador.criar("Carla", passiva="Preciso")
        preciso.d20 = lambda: 19
        preciso.d10 = lambda: 5
        critico = resolver_ataque(preciso, bruno)
        self.assertTrue(critico["critico"])

    def test_nivel_tres_libera_as_outras_magias(self):
        ana = Jogador.criar("Ana", passiva="Bruto")
        ana.experiencia = 99
        ana.ganhar_experiencia(200)
        self.assertGreaterEqual(ana.nivel, 3)
        nomes = {magia.nome for magia in ana.magias}
        self.assertIn("Bola de Fogo", nomes)
        self.assertIn("Rajada Congelante", nomes)


if __name__ == "__main__":
    unittest.main()
