import unittest


class TestMainImport(unittest.TestCase):
    def test_importar_main_nao_inicia_partida(self):
        import main

        self.assertTrue(callable(main.main))
        self.assertTrue(callable(main.jogar))


if __name__ == "__main__":
    unittest.main()
