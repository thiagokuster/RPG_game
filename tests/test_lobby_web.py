import unittest

from equipamento import Equipamento
from web.lobby import Lobby


class TestLobbyWeb(unittest.TestCase):
    def setUp(self):
        self.lobby = Lobby()
        self.room = self.lobby.create_room("Alice")
        self.lobby.join_room("Bob", self.room["code"])
        self.lobby.start_match(self.room["code"], {"Alice": "Guerreiro", "Bob": "Mago"}, token=self.lobby.token_of(self.room["code"], "Alice"))

    def test_snapshot_inclui_magias_inventario_e_loja(self):
        state = self.lobby.get_room(self.room["code"])["room"]
        bob = next(player for player in state["players"] if player["name"] == "Bob")
        self.assertTrue(bob["magias"])
        self.assertIn("shop", state)
        self.assertGreaterEqual(len(state["shop"]), 1)

    def test_loja_inventario_equipamento_e_magia_funcionam(self):
        room = self.lobby.rooms[self.room["code"]]
        alice = next(player["obj"] for player in room["players"] if player["name"] == "Alice")
        alice.moedas = 20

        result = self.lobby.perform_action(self.room["code"], "Alice", "shop", action_type="refresh", token=self.lobby.token_of(self.room["code"], "Alice"))
        self.assertEqual(result["type"], "shop")
        self.assertIn("items", result)
        self.assertEqual(result["next_turn"], "Bob")

        room["current_turn"] = "Alice"
        alice.moedas = 20
        room["shop"] = [Equipamento("Espada do Guardião", dano=8, valor=10, tipo="arma", raridade="raro", bonus_ataque=2)]
        result = self.lobby.perform_action(self.room["code"], "Alice", "shop", item_index=0, token=self.lobby.token_of(self.room["code"], "Alice"))
        self.assertEqual(result["result"], "purchase")
        self.assertEqual(result["next_turn"], "Bob")

        room["current_turn"] = "Alice"
        result = self.lobby.perform_action(self.room["code"], "Alice", "equip", item_index=0, token=self.lobby.token_of(self.room["code"], "Alice"))
        self.assertEqual(result["type"], "inventory")
        self.assertIsNotNone(alice.arma)
        self.assertEqual(result["next_turn"], "Bob")

        result = self.lobby.perform_action(self.room["code"], "Bob", "use_magic", target="Alice", magic="Bola de Fogo", token=self.lobby.token_of(self.room["code"], "Bob"))
        self.assertEqual(result["type"], "magic")
        self.assertEqual(result["next_turn"], "Alice")

    def test_acao_invalida_e_turno_rejeitado(self):
        result = self.lobby.perform_action(self.room["code"], "Alice", "dance")
        self.assertEqual(result["error"], "Ação indisponível neste lobby.")

        room = self.lobby.rooms[self.room["code"]]
        room["current_turn"] = "Bob"
        result = self.lobby.perform_action(self.room["code"], "Alice", "attack", token=self.lobby.token_of(self.room["code"], "Alice"))
        self.assertEqual(result["error"], "Não é sua vez.")


if __name__ == "__main__":
    unittest.main()
