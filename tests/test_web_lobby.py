import unittest
from unittest.mock import patch

from web.limits import RateLimiter, hash_secret
from web.lobby import Lobby


class TestLobby(unittest.TestCase):
    def test_criar_e_entrar_na_sala(self):
        lobby = Lobby()
        created = lobby.create_room("Alice")

        self.assertEqual(created["players"][0]["name"], "Alice")
        self.assertEqual(len(created["players"]), 1)

        joined = lobby.join_room("Bob", created["code"])
        self.assertIn("Bob", [player["name"] for player in joined["players"]])

    def test_iniciar_partida_define_turno_inicial(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])

        match = lobby.start_match(room["code"], classes={"Alice": "Guerreiro", "Bob": "Mago"}, token=lobby.token_of(room["code"], "Alice"))

        self.assertEqual(match["status"], "started")
        self.assertEqual(match["current_turn"], "Alice")
        self.assertEqual(len(match["players"]), 2)

    def test_ataque_avanca_para_o_proximo_turno(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])
        lobby.start_match(room["code"], classes={"Alice": "Guerreiro", "Bob": "Mago"}, token=lobby.token_of(room["code"], "Alice"))

        result = lobby.perform_action(room["code"], "Alice", "attack", "Bob", token=lobby.token_of(room["code"], "Alice"))

        self.assertEqual(result["room"], room["code"])
        self.assertIn(result["next_turn"], ["Alice", "Bob", None])

    def test_turno_pula_jogadores_mortos(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])
        lobby.join_room("Charlie", room["code"])
        lobby.start_match(room["code"], classes={
            "Alice": "Guerreiro",
            "Bob": "Mago",
            "Charlie": "Arqueiro",
        }, token=lobby.token_of(room["code"], "Alice"))

        room_data = lobby.rooms[room["code"]]
        room_data["current_turn"] = "Bob"
        room_data["match"].jogadores[1].hp = 0
        room_data["players"] = [
            {"name": "Alice", "classe": "Guerreiro", "hp": 100, "max_hp": 100, "obj": room_data["match"].jogadores[0]},
            {"name": "Bob", "classe": "Mago", "hp": 0, "max_hp": 100, "obj": room_data["match"].jogadores[1]},
            {"name": "Charlie", "classe": "Arqueiro", "hp": 100, "max_hp": 100, "obj": room_data["match"].jogadores[2]},
        ]

        next_turn = lobby._next_turn(room_data, room_data["match"])

        self.assertEqual(next_turn, "Charlie")
        self.assertEqual(room_data["current_turn"], "Charlie")

    def test_nao_pode_iniciar_partida_com_menos_de_dois_jogadores(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")

        with self.assertRaisesRegex(ValueError, "pelo menos dois jogadores"):
            lobby.start_match(room["code"], token=lobby.token_of(room["code"], "Alice"))

    def test_nao_pode_entrar_com_nome_duplicado(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")

        with self.assertRaisesRegex(ValueError, "já existe"):
            lobby.join_room("Alice", room["code"])

    def test_criar_sala_reutiliza_codigo_do_mesmo_anfitriao(self):
        lobby = Lobby()
        primeira = lobby.create_room("Alice")
        segunda = lobby.create_room("Alice")
        terceira = lobby.create_room("Alice")

        self.assertEqual(primeira["code"], segunda["code"])
        self.assertEqual(segunda["code"], terceira["code"])
        self.assertEqual(len(lobby.list_rooms()["rooms"]), 1)

    def test_sala_recusa_setimo_jogador(self):
        lobby = Lobby()
        room = lobby.create_room("Ana")
        for nome in ["Bruno", "Carla", "Diego", "Eva", "Fabio"]:
            lobby.join_room(nome, room["code"])

        with self.assertRaisesRegex(ValueError, "cheia"):
            lobby.join_room("Gabi", room["code"])
        self.assertEqual(len(lobby.get_room(room["code"])["room"]["players"]), 6)

    def test_sala_protegida_exige_senha(self):
        lobby = Lobby()
        room = lobby.create_room("Alice", password="segredo1")
        self.assertTrue(room["protected"])
        self.assertNotIn("password", room)
        self.assertEqual(lobby.rooms[room["code"]]["password"], hash_secret("segredo1"))
        self.assertNotEqual(lobby.rooms[room["code"]]["password"], "segredo1")

        with self.assertRaisesRegex(ValueError, "Senha"):
            lobby.join_room("Bob", room["code"])
        joined = lobby.join_room("Bob", room["code"], password="segredo1")
        self.assertIn("Bob", [player["name"] for player in joined["players"]])

    def test_rejeita_nome_invalido(self):
        lobby = Lobby()
        with self.assertRaisesRegex(ValueError, "inválidos"):
            lobby.create_room("Ana<script>")

    def test_nao_pode_reiniciar_partida_ja_iniciada(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])
        lobby.start_match(room["code"], classes={"Alice": "Guerreiro", "Bob": "Mago"}, token=lobby.token_of(room["code"], "Alice"))

        with self.assertRaisesRegex(ValueError, "já foi iniciada"):
            lobby.start_match(room["code"], classes={"Alice": "Guerreiro", "Bob": "Mago"}, token=lobby.token_of(room["code"], "Alice"))

    def test_somente_anfitriao_inicia_e_token_impede_impersonacao(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])
        classes = {"Alice": "Guerreiro", "Bob": "Mago"}

        with self.assertRaisesRegex(ValueError, "Sessão inválida"):
            lobby.start_match(room["code"], classes=classes)
        with self.assertRaisesRegex(ValueError, "anfitrião"):
            lobby.start_match(room["code"], classes=classes, token=lobby.token_of(room["code"], "Bob"))

        lobby.start_match(room["code"], classes=classes, token=lobby.token_of(room["code"], "Alice"))
        result = lobby.perform_action(
            room["code"],
            "Alice",
            "attack",
            "Bob",
            token=lobby.token_of(room["code"], "Bob"),
        )
        self.assertEqual(result["error"], "Não é sua vez.")
        snapshot = lobby.get_room(room["code"])["room"]
        self.assertNotIn("token", snapshot)
        self.assertNotIn("tokens", snapshot)

    def test_ataque_concede_experiencia_e_cura_nao_ressuscita(self):
        lobby = Lobby()
        room = lobby.create_room("Alice")
        lobby.join_room("Bob", room["code"])
        lobby.start_match(
            room["code"],
            classes={"Alice": "Guerreiro", "Bob": "Mago"},
            token=lobby.token_of(room["code"], "Alice"),
        )
        partida = lobby.rooms[room["code"]]["match"]
        alice, bob = partida.jogadores
        xp_antes = alice.experiencia
        with patch.object(alice, "d20", return_value=20):
            result = lobby.perform_action(
                room["code"],
                "Alice",
                "attack",
                "Bob",
                token=lobby.token_of(room["code"], "Alice"),
            )
        self.assertEqual(result["result"], "hit")
        self.assertGreaterEqual(alice.experiencia, xp_antes + 25)

        lobby.rooms[room["code"]]["current_turn"] = "Bob"
        alice.hp = 0
        cura = lobby.perform_action(
            room["code"],
            "Bob",
            "use_magic",
            target="Alice",
            magic="Cura Leve",
            token=lobby.token_of(room["code"], "Bob"),
        )
        self.assertEqual(cura.get("type"), "error")
        self.assertEqual(alice.hp, 0)


class TestRateLimiter(unittest.TestCase):
    def test_bloqueia_apos_o_limite_por_origem(self):
        limiter = RateLimiter(limit=2, window=60)
        self.assertTrue(limiter.check("127.0.0.1"))
        self.assertTrue(limiter.check("127.0.0.1"))
        self.assertFalse(limiter.check("127.0.0.1"))
        self.assertTrue(limiter.check("10.0.0.2"))


if __name__ == "__main__":
    unittest.main()
