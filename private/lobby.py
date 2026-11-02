import random
from threading import Lock

from combate import resolver_ataque
from equipamento import Equipamento
from jogador import Jogador
from partida import Partida
from private.limits import (
    ALLOWED_ACTIONS,
    ALLOWED_CLASSES,
    issue_token,
    sanitize_magic,
    sanitize_name,
    sanitize_password,
    sanitize_room,
    token_matches,
)


class PrivateLobby:
    MAX_PLAYERS = 6

    def __init__(self):
        self.rooms = {}
        self._lock = Lock()

    @staticmethod
    def _generate_code_for_lobby(existing_rooms):
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(random.choice(alphabet) for _ in range(6))
            if code not in existing_rooms:
                return code

    def _serialize_player(self, player):
        obj = player.get("obj")
        if obj is not None:
            return {
                "name": obj.nome,
                "classe": obj.classe,
                "hp": obj.hp,
                "max_hp": obj.max_hp,
                "moedas": obj.moedas,
                "mana": obj.mana,
                "max_mana": obj.max_mana,
                "nivel": obj.nivel,
                "armor_class": obj.armor_class,
                "sorte": obj.sorte,
                "arma": obj.arma.nome if obj.arma else None,
                "armadura": obj.armadura.nome if obj.armadura else None,
                "inventory": [
                    {
                        "nome": item.nome,
                        "tipo": item.tipo,
                        "raridade": getattr(item, "raridade", None),
                        "durabilidade": getattr(item, "durabilidade", 0),
                    }
                    for item in obj.inventario
                ],
                "magias": [{"nome": magia.nome, "tipo": magia.tipo, "custo": magia.custo} for magia in obj.magias],
            }
        return {
            "name": player["name"],
            "classe": player.get("classe", "Guerreiro"),
            "hp": player.get("hp", 0),
            "max_hp": player.get("max_hp", 0),
            "moedas": 0,
            "mana": 0,
            "max_mana": 0,
            "nivel": 1,
            "armor_class": player.get("armor_class", 12),
            "arma": None,
            "inventory": [],
            "magias": [],
        }

    def _append_log(self, room, text):
        logs = room.setdefault("log", [])
        logs.append({"text": text})
        room["log"] = logs[-40:]

    def _room_snapshot(self, room_code):
        room = self.rooms.get(room_code)
        if room is None:
            return None
        return {
            "code": room_code,
            "players": [self._serialize_player(player) for player in room["players"]],
            "status": room.get("status", "waiting"),
            "current_turn": room.get("current_turn"),
            "winner": room.get("winner"),
            "shop": [self._serialize_item(item) for item in room.get("shop", [])],
            "log": list(room.get("log", [])),
            "protected": bool(room.get("password")),
        }

    @staticmethod
    def _make_player(name, classe="Guerreiro"):
        jogador = Jogador.criar_por_classe(name, classe)
        return {
            "name": jogador.nome,
            "classe": jogador.classe,
            "hp": jogador.hp,
            "max_hp": jogador.max_hp,
            "obj": jogador,
        }

    def _attach_session(self, snapshot, room, name):
        if snapshot is None:
            return None
        snapshot["token"] = room["tokens"][name]
        snapshot["player"] = name
        return snapshot

    def _issue_player_token(self, room, name):
        tokens = room.setdefault("tokens", {})
        tokens[name] = issue_token()
        return tokens[name]

    def _player_from_token(self, room, token):
        for name, stored in room.get("tokens", {}).items():
            if token_matches(stored, token):
                return name
        raise ValueError("Sessão inválida.")

    def token_of(self, room_code, player_name):
        room_name = sanitize_room(room_code)
        name = sanitize_name(player_name)
        room = self.rooms.get(room_name)
        if room is None:
            raise KeyError(f"Sala {room_name} não encontrada.")
        token = room.get("tokens", {}).get(name)
        if not token:
            raise ValueError("Sessão inválida.")
        return token

    def create_room(self, player_name, password=None):
        name = sanitize_name(player_name)
        senha = sanitize_password(password)

        with self._lock:
            for code, room in self.rooms.items():
                if room.get("status") != "waiting":
                    continue
                host = room["players"][0]["name"] if room.get("players") else None
                if host == name:
                    room.setdefault("tokens", {})
                    if name not in room["tokens"]:
                        self._issue_player_token(room, name)
                    return self._attach_session(self._room_snapshot(code), room, name)

            code = self._generate_code_for_lobby(self.rooms)
            room = {
                "code": code,
                "players": [self._make_player(name)],
                "status": "waiting",
                "current_turn": None,
                "winner": None,
                "turn_order": [name],
                "match": None,
                "password": senha or None,
                "tokens": {},
                "rodada": 1,
                "log": [{"text": f"{name} criou a sala."}],
            }
            self._issue_player_token(room, name)
            self.rooms[code] = room
            return self._attach_session(self._room_snapshot(code), room, name)

    def join_room(self, player_name, room_code, password=None):
        room_name = sanitize_room(room_code)
        name = sanitize_name(player_name)
        senha = sanitize_password(password)

        with self._lock:
            room = self.rooms.get(room_name)
            if room is None:
                raise KeyError(f"Sala {room_name} não encontrada.")
            if room.get("password") and room["password"] != senha:
                raise ValueError("Senha da sala inválida.")
            if room.get("status") == "started" and room.get("match") is not None:
                raise ValueError("A partida já foi iniciada. Não é possível entrar na sala durante o jogo.")
            if any(player["name"] == name for player in room["players"]):
                raise ValueError(f"O jogador {name} já existe nesta sala.")
            if len(room["players"]) >= self.MAX_PLAYERS:
                raise ValueError(f"A sala já está cheia (máximo {self.MAX_PLAYERS} jogadores).")

            room["players"].append(self._make_player(name))
            room["turn_order"].append(name)
            self._issue_player_token(room, name)
            self._append_log(room, f"{name} entrou na sala.")
            return self._attach_session(self._room_snapshot(room_name), room, name)

    def start_match(self, room_code, classes=None, token=None):
        room_name = sanitize_room(room_code)
        with self._lock:
            room = self.rooms.get(room_name)
            if room is None:
                raise KeyError(f"Sala {room_name} não encontrada.")
            requester = self._player_from_token(room, token)
            host = room["players"][0]["name"] if room.get("players") else None
            if requester != host:
                raise ValueError("Somente o anfitrião pode iniciar a partida.")
            if room.get("status") == "started" and room.get("match") is not None:
                raise ValueError("A partida já foi iniciada.")

            player_names = [player["name"] for player in room["players"]]
            if len(player_names) < 2:
                raise ValueError("É necessário pelo menos dois jogadores para iniciar a partida.")

            selected_classes = classes or {}
            unknown_players = [name for name in player_names if name not in selected_classes]
            if unknown_players:
                raise ValueError("Defina uma classe para todos os jogadores antes de iniciar.")
            invalid_classes = [classe for classe in selected_classes.values() if classe not in ALLOWED_CLASSES]
            if invalid_classes:
                raise ValueError("Classe inválida.")

            jogadores = [Jogador.criar_por_classe(nome, selected_classes[nome]) for nome in player_names]
            partida = Partida(jogadores)

            room["match"] = partida
            room["shop"] = Equipamento.gerar_estoque(1, 3)
            room["status"] = "started"
            room["turn_order"] = player_names
            room["current_turn"] = player_names[0]
            room["rodada"] = 1
            room["winner"] = None
            room["players"] = [
                {"name": jogador.nome, "classe": jogador.classe, "hp": jogador.hp, "max_hp": jogador.max_hp, "obj": jogador}
                for jogador in partida.jogadores
            ]
            self._append_log(room, f"Partida iniciada. Vez de {room['current_turn']}.")
            partida.jogadores[0].iniciar_turno()
            return self._room_snapshot(room_name)

    def list_rooms(self):
        with self._lock:
            rooms = []
            for code, room in sorted(self.rooms.items()):
                if room.get("status") not in {"waiting", "started"}:
                    continue
                players = [
                    {"name": player["name"], "classe": player["classe"], "hp": player["hp"], "max_hp": player["max_hp"]}
                    for player in room["players"]
                ]
                rooms.append({
                    "code": code,
                    "players": players,
                    "status": room.get("status", "waiting"),
                    "protected": bool(room.get("password")),
                })
            return {"rooms": rooms}

    def get_room(self, room_code):
        room_name = sanitize_room(room_code)
        with self._lock:
            room = self.rooms.get(room_name)
            if room is None:
                raise KeyError(f"Sala {room_name} não encontrada.")
            return {"room": self._room_snapshot(room_name)}

    def _next_turn(self, room, match=None):
        match = match or room.get("match")
        jogadores = match.jogadores
        vivos = [jogador for jogador in jogadores if jogador.hp > 0]
        if not vivos:
            room["current_turn"] = None
            room["winner"] = "nenhum"
            room["status"] = "finished"
            return None

        atual = next((jogador for jogador in jogadores if jogador.nome == room.get("current_turn")), None)
        if atual is None:
            room["current_turn"] = vivos[0].nome
            vivos[0].iniciar_turno()
            return room["current_turn"]

        indice = jogadores.index(atual)
        for passo in range(1, len(jogadores) + 1):
            candidato = jogadores[(indice + passo) % len(jogadores)]
            if candidato.hp > 0:
                room["current_turn"] = candidato.nome
                candidato.iniciar_turno()
                if jogadores.index(candidato) <= indice:
                    match.iniciar_rodada()
                    room["rodada"] = room.get("rodada", 1) + 1
                return candidato.nome
        room["current_turn"] = None
        return None

    def _sync_players(self, room, match):
        room["players"] = [
            {"name": jogador.nome, "classe": jogador.classe, "hp": jogador.hp, "max_hp": jogador.max_hp, "obj": jogador}
            for jogador in match.jogadores
        ]

    def _log_action(self, room, result):
        player = result.get("player")
        if result.get("result") == "miss":
            self._append_log(room, f"{player} errou o ataque em {result.get('target')}.")
        elif result.get("result") == "hit":
            self._append_log(room, f"{player} atacou {result.get('target')} e causou {result.get('damage', 0)} de dano.")
        elif result.get("type") == "magic":
            self._append_log(room, f"{player} lançou {result.get('magic')} em {result.get('target')}.")
        elif result.get("type") == "shop" and result.get("result") == "purchase":
            self._append_log(room, f"{player} comprou {result.get('item')}.")
        elif result.get("type") == "shop":
            self._append_log(room, f"{player} atualizou a loja.")
        elif result.get("type") == "inventory":
            self._append_log(room, f"{player} equipou {result.get('item')}.")
        if result.get("status") == "finished":
            winner = result.get("winner")
            if winner and winner != "nenhum":
                self._append_log(room, f"Fim de partida. {winner} venceu.")
            else:
                self._append_log(room, "Fim de partida. Sem vencedor.")

    def _concluir(self, room, room_name, result):
        match = room["match"]
        match.verificar_mortos()
        self._sync_players(room, match)
        if match.fim_partida():
            room["status"] = "finished"
            room["winner"] = match.vivos()[0].nome if match.vivos() else "nenhum"
            room["current_turn"] = None
            result["status"] = "finished"
            result["winner"] = room["winner"]
            result["next_turn"] = None
        else:
            atacante = next((j for j in match.jogadores if j.nome == result.get("player")), None)
            if result.get("type") == "magic" and atacante is not None and not getattr(atacante, "gasta_turno", True):
                atacante.gasta_turno = True
                result["next_turn"] = atacante.nome
                result["extra"] = True
                room["current_turn"] = atacante.nome
            else:
                result["next_turn"] = self._next_turn(room, match)
            result["status"] = room["status"]
        result["current_turn"] = room.get("current_turn")
        result["room"] = room_name
        self._log_action(room, result)
        result["room_state"] = self._room_snapshot(room_name)
        return result

    def perform_action(self, room_code, player_name=None, action="attack", target=None, item_index=None, action_type=None, magic=None, token=None):
        room_name = sanitize_room(room_code)
        if action not in ALLOWED_ACTIONS:
            return {"error": "Ação indisponível neste lobby.", "current_turn": None}

        with self._lock:
            room = self.rooms.get(room_name)
            if room is None:
                raise KeyError(f"Sala {room_name} não encontrada.")
            player = self._player_from_token(room, token)
            if room.get("status") != "started" or room.get("match") is None:
                raise ValueError("A partida ainda não foi iniciada.")
            if room["current_turn"] != player:
                return {"error": "Não é sua vez.", "current_turn": room["current_turn"]}

            match = room["match"]
            atacante = next((j for j in match.jogadores if j.nome == player), None)
            if atacante is None:
                return {"error": "Jogador não encontrado na partida.", "current_turn": room["current_turn"]}

            if action == "attack":
                alvo_nome = target or next((j.nome for j in match.jogadores if j.nome != player and j.hp > 0), None)
                alvo = next((j for j in match.jogadores if j.nome == alvo_nome), None)
                if alvo is None or alvo.hp <= 0:
                    return {"error": "Alvo inválido.", "current_turn": room["current_turn"]}
                resultado = resolver_ataque(atacante, alvo)
                if resultado["acertou"]:
                    Partida.ganhar_moeda(atacante, room.get("rodada", 1), silencioso=True)
                    atacante.ganhar_experiencia(25)
                return self._concluir(room, room_name, {
                    "player": player,
                    "target": alvo.nome,
                    "result": "hit" if resultado["acertou"] else "miss",
                    "damage": resultado["dano"],
                })

            if action == "shop":
                if action_type == "refresh":
                    if atacante.moedas < 5:
                        return {"error": "Moedas insuficientes.", "current_turn": room["current_turn"]}
                    atacante.moedas -= 5
                    nivel = match.jogadores[0].nivel if match.jogadores else 1
                    room["shop"] = Equipamento.gerar_estoque(nivel, 3)
                    return self._concluir(room, room_name, {
                        "type": "shop",
                        "player": player,
                        "items": [self._serialize_item(item) for item in room["shop"]],
                    })
                if item_index is None or not isinstance(item_index, int):
                    return {"type": "error", "message": "Item inválido."}
                if not 0 <= item_index < len(room.get("shop", [])):
                    return {"type": "error", "message": "Item inválido."}
                item = room["shop"][item_index]
                if atacante.moedas < item.valor:
                    return {"type": "error", "message": "Moedas insuficientes."}
                atacante.moedas -= item.valor
                atacante.adicionar_item_inventario(item)
                del room["shop"][item_index]
                return self._concluir(room, room_name, {
                    "type": "shop",
                    "player": player,
                    "result": "purchase",
                    "item": item.nome,
                    "inventory": [item.nome for item in atacante.inventario],
                })

            if action == "equip":
                if item_index is None or not isinstance(item_index, int) or not 0 <= item_index < len(atacante.inventario):
                    return {"type": "error", "message": "Item inválido."}
                item = atacante.inventario[item_index]
                atacante.equipar(item)
                return self._concluir(room, room_name, {
                    "type": "inventory",
                    "player": atacante.nome,
                    "result": "equip",
                    "item": item.nome,
                })

            if action == "use_magic":
                alvo = next((j for j in match.jogadores if j.nome == target), None)
                magia = next((m for m in atacante.magias if m.nome.lower() == sanitize_magic(magic).lower()), None)
                if alvo is None or magia is None:
                    return {"type": "error", "message": "Magia inválida."}
                if magia.tipo == "cura" and alvo.hp <= 0:
                    return {"type": "error", "message": "Não é possível curar um jogador eliminado."}
                if magia.tipo == "dano" and alvo.hp <= 0:
                    return {"type": "error", "message": "O alvo já está morto."}
                if not atacante.usar_magia(magia.nome, alvo):
                    return {"type": "error", "message": "Magia indisponível."}
                return self._concluir(room, room_name, {
                    "type": "magic",
                    "player": atacante.nome,
                    "target": alvo.nome,
                    "magic": magia.nome,
                    "target_hp": alvo.hp,
                })

            return {"error": "Ação indisponível neste lobby.", "current_turn": room["current_turn"]}

    @staticmethod
    def _serialize_item(item):
        return {
            "nome": item.nome,
            "valor": item.valor,
            "tipo": item.tipo,
            "raridade": item.raridade,
            "dano": item.dano,
            "armadura": item.armadura,
            "bonus_ataque": item.bonus_ataque,
            "agilidade": getattr(item, "agilidade", 0),
            "reducao": getattr(item, "reducao", 0),
            "durabilidade": getattr(item, "durabilidade", 0),
            "max_durabilidade": getattr(item, "max_durabilidade", 0),
        }
