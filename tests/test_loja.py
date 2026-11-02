import unittest

from equipamento import Equipamento
from loja import Loja


class TestLoja(unittest.TestCase):
    def test_estoque_inicial_separa_categorias(self):
        loja = Loja()
        self.assertEqual(len(loja.estoque), 3)
        tipos = [item.tipo for item in loja.estoque]
        self.assertEqual(tipos, ["arma", "armadura", "anel"])
        self.assertTrue(all(item.raridade for item in loja.estoque))
        self.assertTrue(all(item.nome for item in loja.estoque))

    def test_armadura_gerada_tem_reducao_e_durabilidade(self):
        peca = Equipamento.gerar_por_categoria(3, "armadura")
        self.assertEqual(peca.tipo, "armadura")
        self.assertGreater(peca.reducao, 0)
        self.assertGreater(peca.durabilidade, 0)
        self.assertIn("redução", peca.descricao())


if __name__ == "__main__":
    unittest.main()
