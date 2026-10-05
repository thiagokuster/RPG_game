import unittest
from unittest.mock import patch

from jogador.jogador import Jogador
from monstro import Monstro
from partida.partida import Partida


class TestSistemaAvancado(unittest.TestCase):
    def test_jogador_criado_com_classe_mago(self):
        jogador = Jogador.criar_por_classe("Merlin", "Mago")
        self.assertEqual(jogador.classe, "Mago")
        self.assertGreaterEqual(jogador.armor_class, 10)
        self.assertTrue(jogador.magias)

    def test_monstro_gerado_com_nivel(self):
        monstro = Monstro.gerar_monstro(2)
        self.assertTrue(monstro.nome)
        self.assertGreater(monstro.hp, 0)
        self.assertGreater(monstro.dano, 0)

    def test_evento_monstro_nao_ativa_tarde_demais_no_inicio(self):
        partida = Partida([Jogador.criar_por_classe("A", "Guerreiro")])
        with patch("partida.partida.randint", return_value=3):
            evento = partida.gerar_evento_monstro(rodada=1)
            self.assertIsNone(evento)

    def test_partida_termina_apenas_com_um_vivo(self):
        partida = Partida([
            Jogador.criar_por_classe("A", "Guerreiro"),
            Jogador.criar_por_classe("B", "Guerreiro"),
        ])
        self.assertFalse(partida.fim_partida())

        partida.jogadores = [Jogador.criar_por_classe("C", "Guerreiro")]
        self.assertTrue(partida.fim_partida())

    def test_partida_termina_quando_todos_morrem(self):
        partida = Partida([
            Jogador.criar_por_classe("A", "Guerreiro"),
            Jogador.criar_por_classe("B", "Guerreiro"),
        ])
        partida.jogadores = []
        self.assertTrue(partida.fim_partida())


if __name__ == "__main__":
    unittest.main()
