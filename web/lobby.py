import random
from threading import Lock

from equipamento import Equipamento
from jogador import Jogador
from partida import Partida
from sala.acoes import resolver_jogada, serializar_eventos
from web.limits import (
    ALLOWED_ACTIONS,
    hash_secret,
    issue_token,
    new_salt,
    sanitize_magic,
    sanitize_name,
    sanitize_password,
    sanitize_room,
    token_matches,
)


class Lobby:
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
            inventario = getattr(obj, "inventario", []) or []
            magias = getattr(obj, "magias", []) or []
            arma = getattr(obj, "arma", None)
            armadura = getattr(obj, "armadura", None)
            return {
                "name": obj.nome,
                "classe": getattr(obj, "classe", "Aventureiro"),
                "hp": obj.hp,
                "max_hp": getattr(obj, "max_hp", obj.hp),
                "moedas": getattr(obj, "moedas", 0),
                "mana": getattr(obj, "mana", 0),
                "max_mana": getattr(obj, "max_mana", 0),
                "nivel": getattr(obj, "nivel", 1),
                "armor_class": getattr(obj, "armor_class", 12),
                "sorte": getattr(obj, "sorte", 0),
                "arma": arma.nome if arma else None,
                "armadura": armadura.nome if armadura else None,
                "npc": not hasattr(obj, "inventario"),
                "passiva": getattr(obj, "passiva", None),
                "inventory": [
                    {
                        "nome": item.nome,
                        "tipo": item.tipo,
                        "raridade": getattr(item, "raridade", None),
                        "durabilidade": getattr(item, "durabilidade", 0),
                    }
                    for item in inventario
                ],
                "magias": [{"nome": magia.nome, "tipo": magia.tipo, "custo": magia.custo} for magia in magias],
            }
        return {
            "name": player["name"],
            "classe": player.get("classe", "Aventureiro"),
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
            "eventos": list(room.get("eventos", [])),
            "protected": bool(room.get("password")),
            "modo": room.get("modo", "pvp"),
        }

    @staticmethod
    def _make_player(name, classe=None):
        jogador = Jogador.criar(name, passiva=classe)
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
            salt = new_salt()
            room = {
                "code": code,
                "players": [self._make_player(name)],
                "status": "waiting",
                "current_turn": None,
                "winner": None,
                "turn_order": [name],
                "match": None,
                "password_salt": salt,
                "password": hash_secret(senha, salt) or None,
                "tokens": {},
                "rodada": 1,
                "log": [{"text": f"{name} criou a sala."}],
                "eventos": [],
                "modo": "pvp",
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
            if room.get("password") and room["password"] != hash_secret(senha, room.get("password_salt", "")):
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

    def start_match(self, room_code, classes=None, token=None, modo="pvp"):
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

            escolhas = classes if isinstance(classes, dict) else {}
            jogadores = Jogador.criar_elenco(player_names, escolhas)
            modo_sala = "coop" if str(modo).lower() == "coop" else "pvp"
            partida = Partida(jogadores, modo=modo_sala)
            ondas = []
            if modo_sala == "coop":
                ondas = self._emitir(partida, partida.tentar_proxima_onda())

            room["match"] = partida
            room["modo"] = modo_sala
            room["shop"] = Equipamento.gerar_estoque(1, 3)
            room["status"] = "started"
            room["turn_order"] = [jogador.nome for jogador in partida.jogadores]
            room["current_turn"] = player_names[0]
            room["rodada"] = 1
            room["winner"] = None
            room["eventos"] = list(ondas)
            room["players"] = [
                {"name": jogador.nome, "classe": jogador.classe, "hp": jogador.hp, "max_hp": jogador.max_hp, "obj": jogador}
                for jogador in partida.jogadores
            ]
            self._append_log(room, f"Partida iniciada. Vez de {room['current_turn']}.")
            for ev in ondas:
                if ev.get("texto"):
                    self._append_log(room, ev["texto"])
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
            if hasattr(vivos[0], "iniciar_turno"):
                vivos[0].iniciar_turno()
            return room["current_turn"]

        indice = jogadores.index(atual)
        for passo in range(1, len(jogadores) + 1):
            candidato = jogadores[(indice + passo) % len(jogadores)]
            if candidato.hp > 0:
                room["current_turn"] = candidato.nome
                if hasattr(candidato, "iniciar_turno"):
                    candidato.iniciar_turno()
                if jogadores.index(candidato) <= indice:
                    match.iniciar_rodada()
                    room["rodada"] = room.get("rodada", 1) + 1
                return candidato.nome
        room["current_turn"] = None
        return None

    def _eh_npc(self, jogador):
        return not hasattr(jogador, "inventario")

    def _emitir(self, match, eventos):
        return serializar_eventos(match.carimbar(eventos))

    def _resolver_turno_npc(self, room, match):
        atual = next((jogador for jogador in match.jogadores if jogador.nome == room.get("current_turn")), None)
        while atual is not None and self._eh_npc(atual) and room.get("status") == "started":
            alvos = [jogador for jogador in match.jogadores if not self._eh_npc(jogador) and jogador.hp > 0]
            if not alvos:
                break
            acao = atual.agir if hasattr(atual, "agir") else atual.atacar
            resultado = acao(alvos) if acao is atual.agir else atual.atacar(alvos[0])
            eventos = self._emitir(match, resultado.get("eventos") if isinstance(resultado, dict) else [resultado])
            room["eventos"] = (list(room.get("eventos") or []) + eventos)[-40:]
            for ev in eventos:
                if ev.get("texto"):
                    self._append_log(room, ev["texto"])
            match.verificar_mortos()
            extra = self._emitir(match, match.tentar_proxima_onda())
            if extra:
                room["eventos"] = (room["eventos"] + extra)[-40:]
                self._sync_players(room, match)
            if match.fim_partida():
                room["status"] = "finished"
                room["winner"] = match.resultado_fim().get("vencedor") or "nenhum"
                room["current_turn"] = None
                return
            self._next_turn(room, match)
            atual = next((jogador for jogador in match.jogadores if jogador.nome == room.get("current_turn")), None)

    def _sync_players(self, room, match):
        room["players"] = [
            {"name": jogador.nome, "classe": jogador.classe, "hp": jogador.hp, "max_hp": jogador.max_hp, "obj": jogador}
            for jogador in match.jogadores
        ]

    def _log_action(self, room, result):
        for ev in result.get("eventos") or []:
            texto = ev.get("texto") or ev.get("motivo")
            if texto:
                self._append_log(room, texto)
        if result.get("status") == "finished":
            winner = result.get("winner")
            if winner and winner != "nenhum":
                self._append_log(room, f"Fim de partida. {winner} venceu.")
            else:
                self._append_log(room, "Fim de partida. Sem vencedor.")

    def _concluir(self, room, room_name, result):
        match = room["match"]
        match.verificar_mortos()
        extra = self._emitir(match, match.tentar_proxima_onda())
        if extra:
            room["eventos"] = (list(room.get("eventos") or []) + extra)[-40:]
            result["eventos"] = list(room["eventos"])
        self._sync_players(room, match)
        if match.fim_partida():
            room["status"] = "finished"
            room["winner"] = match.resultado_fim().get("vencedor") or "nenhum"
            room["current_turn"] = None
            result["status"] = "finished"
            result["winner"] = room["winner"]
            result["next_turn"] = None
        else:
            result["next_turn"] = self._next_turn(room, match)
            self._resolver_turno_npc(room, match)
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

            jogada = resolver_jogada(
                match,
                atacante,
                action,
                alvo_nome=target,
                magia=sanitize_magic(magic) if magic else None,
                item_index=item_index,
                action_type=action_type,
                shop=room.get("shop", []),
                rodada=room.get("rodada", 1),
            )
            if not jogada.get("ok"):
                return {
                    "error": jogada.get("erro") or "Ação inválida.",
                    "type": "error",
                    "message": jogada.get("erro") or "Ação inválida.",
                    "current_turn": room["current_turn"],
                }
            if "shop" in jogada:
                room["shop"] = jogada["shop"]
            eventos = self._emitir(match, jogada.get("eventos"))
            room["eventos"] = (list(room.get("eventos") or []) + eventos)[-40:]
            payload = {
                "player": player,
                "target": jogada.get("target") or target,
                "result": jogada.get("result"),
                "damage": jogada.get("damage", 0),
                "critico": jogada.get("critico", False),
                "type": jogada.get("type"),
                "magic": jogada.get("magic"),
                "item": jogada.get("item"),
                "eventos": list(room["eventos"]),
                "items": [self._serialize_item(item) for item in room.get("shop", [])],
                "inventory": [item.nome for item in atacante.inventario],
            }
            return self._concluir(room, room_name, payload)

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
