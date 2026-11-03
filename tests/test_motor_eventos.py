import unittest

from combate import resolver_ataque
from jogador import Jogador
from motor.eventos import texto


class TestMotorEventos(unittest.TestCase):
    def test_ataque_devolve_evento_sem_io(self):
        ana = Jogador.criar("Ana", passiva="Bruto")
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        ana.d20 = lambda: 20
        ana.d10 = lambda: 5
        resultado = resolver_ataque(ana, bruno)
        self.assertEqual(resultado["tipo"], "ataque")
        self.assertEqual(resultado["de"], "Ana")
        self.assertEqual(resultado["para"], "Bruno")
        self.assertTrue(resultado["acertou"])
        self.assertTrue(resultado["critico"])
        self.assertTrue(resultado["eventos"])
        self.assertIn("atacou", texto(resultado["eventos"][0]))

    def test_magia_devolve_evento(self):
        bruno = Jogador.criar("Bruno", passiva="Arcano")
        ana = Jogador.criar("Ana", passiva="Bruto")
        resultado = bruno.usar_magia("Bola de Fogo", ana)
        self.assertEqual(resultado["tipo"], "magia")
        self.assertEqual(resultado["de"], "Bruno")
        self.assertGreater(resultado["dano"], 0)


if __name__ == "__main__":
    unittest.main()
