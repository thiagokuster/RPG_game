import unittest
from unittest.mock import patch

from equipamento import Equipamento
from jogador import Jogador
from loja import Loja
from magia import Magia
from monstro import Monstro
from partida import Partida


class TestFluxoCompletoPartida(unittest.TestCase):
    def test_jogadores_completam_loja_magias_monstros_equipamento(self):
        guerreiro = Jogador.criar_por_classe("Guerreiro", "Guerreiro")
        guerreiro.magias.append(Magia.bola_de_fogo())
        mago = Jogador.criar_por_classe("Mago", "Mago")
        partida = Partida([guerreiro, mago])
        loja = Loja()

        loja.estoque = [
            Equipamento("Espada do Guardião", dano=8, valor=10, tipo="arma", raridade="raro", bonus_ataque=2),
            Equipamento("Peitoral do Valor", dano=0, valor=10, tipo="armadura", raridade="comum", armadura=3),
        ]

        guerreiro.moedas = 20
        mago.moedas = 20

        with patch("builtins.input", side_effect=[0, -1]):
            loja.entrar_loja(guerreiro)

        self.assertIn("Espada do Guardião", [item.nome for item in guerreiro.inventario])
        guerreiro.equipar(next(item for item in guerreiro.inventario if item.nome == "Espada do Guardião"))
        self.assertEqual(guerreiro.arma.nome, "Espada do Guardião")
        self.assertEqual(guerreiro.ataque_bonus, 4)

        with patch("builtins.input", side_effect=[0, -1]):
            loja.entrar_loja(guerreiro)

        self.assertIn("Peitoral do Valor", [item.nome for item in guerreiro.inventario])
        guerreiro.equipar(next(item for item in guerreiro.inventario if item.nome == "Peitoral do Valor"))
        self.assertEqual(guerreiro.armadura.nome, "Peitoral do Valor")
        self.assertEqual(guerreiro.armor_class, 17)

        mago.hp = 25
        mago.usar_magia("Cura Leve", mago)
        self.assertEqual(mago.hp, 42)

        monstro = Monstro("Goblin Chefe", hp=30, ataque_bonus=5, armor_class=12, dano=8, xp=40, recompensa=15)
        guerreiro.mana = 2

        with patch.object(guerreiro, "d20", return_value=20), \
             patch.object(guerreiro, "d10", return_value=5), \
             patch.object(mago, "d20", return_value=1), \
             patch.object(mago, "d10", return_value=5), \
             patch.object(monstro, "atacar", return_value=8):
            resultado = guerreiro.usar_magia("Bola de Fogo", monstro)
            self.assertTrue(resultado)
            self.assertEqual(monstro.hp, 10)

        self.assertEqual(guerreiro.arma.bonus_ataque, 2)
        self.assertEqual(guerreiro.armor_class, 17)
        self.assertEqual(mago.hp, 42)

        batalha = Partida([guerreiro, mago])
        batalha.jogadores = [guerreiro, mago]
        guerreiro.hp = 1
        mago.hp = 0
        batalha.verificar_mortos()
        self.assertEqual(len(batalha.vivos()), 1)
        self.assertTrue(batalha.fim_partida())
        self.assertEqual(batalha.vivos()[0].nome, "Guerreiro")


if __name__ == "__main__":
    unittest.main()
