import json
import random
import socket
import threading
from pathlib import Path

from equipamento import Equipamento
from jogador import Jogador
from partida import Partida
from sala.acoes import resolver_jogada, serializar_eventos
from web.limits import RateLimiter, hash_secret, new_salt, sanitize_name, sanitize_password

from .protocol import receive_message, send_message


class LobbyServer:
    MAX_PLAYERS = 6

    def __init__(self, host="127.0.0.1", port=5000, state_path=None):
        self.host = host
        self.port = port
        self.state_path = Path(state_path) if state_path else Path("data") / "rooms.json"
        self.rooms = {}
        self.connections = {}
        self.room_state = {}
        self.lock = threading.Lock()
        self.limiter = RateLimiter(limit=40, window=10)
        self.join_limiter = RateLimiter(limit=8, window=60)
        self._ensure_state_file()
        self.load_state()

    def _ensure_room_state(self, room_name):
        if room_name not in self.room_state:
            self.room_state[room_name] = {"order": [], "current_turn": None, "status": "waiting", "match": None}
        return self.room_state[room_name]

    def _current_state_game(self, room_name):
        state = self.room_state.get(room_name)
        return state.get("match") if state else None

    def _room_members(self, room_name):
        return self.rooms.get(room_name, [])

    def _player_names(self, values):
        names = []
        for value in values or []:
            if isinstance(value, str):
                names.append(value)
            elif isinstance(value, dict):
                nome = value.get("nome") or value.get("name") or value.get("player")
                if nome:
                    names.append(nome)
        return names

    def _expected_names(self, state):
        match = state.get("match")
        if match is not None:
            return [jogador.nome for jogador in match.jogadores]
        return self._player_names(state.get("saved_order") or state.get("players") or [])

    def _rebuild_order(self, room_name):
        state = self._ensure_room_state(room_name)
        members = self._room_members(room_name)
        name_to_conn = {
            self.connections[conn]["player"]: conn
            for conn in members
            if conn in self.connections
        }
        saved = self._player_names(state.get("saved_order") or state.get("players") or [])
        order = [name_to_conn[nome] for nome in saved if nome in name_to_conn]
        for conn in members:
            if conn not in order:
                order.append(conn)
        state["order"] = order
        saved_turn = state.get("saved_current_turn")
        if saved_turn in name_to_conn:
            state["current_turn"] = name_to_conn[saved_turn]
        elif state.get("current_turn") not in order:
            state["current_turn"] = order[0] if order else None
        return state

    def _advance_turn(self, room_name):
        state = self.room_state.get(room_name)
        if not state:
            return

        order = state["order"]
        if not order:
            state["current_turn"] = None
            return

        match = state.get("match")
        current = state.get("current_turn")
        start_index = order.index(current) if current in order else -1
        for passo in range(1, len(order) + 1):
            conn = order[(start_index + passo) % len(order)]
            if match is None:
                state["current_turn"] = conn
                return
            nome = self.connections.get(conn, {}).get("player")
            jogador = next((j for j in match.jogadores if j.nome == nome), None)
            if jogador is not None and jogador.hp > 0:
                state["current_turn"] = conn
                state["saved_current_turn"] = nome
                jogador.iniciar_turno()
                if start_index >= 0 and order.index(conn) <= start_index:
                    match.iniciar_rodada()
                    state["rodada"] = state.get("rodada", 1) + 1
                return
        state["current_turn"] = None

    def _set_current_turn(self, room_name, conn):
        state = self._ensure_room_state(room_name)
        order = state["order"]
        if conn not in order:
            return
        state["current_turn"] = conn

    def _room_snapshot(self, room_name):
        state = self.room_state.get(room_name, {})
        order = state.get("order", [])
        current_turn = state.get("current_turn")
        players = [self.connections.get(conn, {}).get("player") for conn in order if conn in self.connections]
        return {
            "room": room_name,
            "players": players,
            "order": players,
            "current_turn": self.connections.get(current_turn, {}).get("player") if current_turn else None,
        }

    def _generate_room_code(self):
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(random.choice(alphabet) for _ in range(6))
            if code not in self.rooms and code not in self.room_state:
                return code

    def _waiting_room_for_host(self, player_name):
        for room_name, members in self.rooms.items():
            state = self.room_state.get(room_name, {})
            if state.get("match") is not None or state.get("status") not in {None, "waiting"}:
                continue
            host_conn = members[0] if members else None
            host = self.connections.get(host_conn, {}).get("player") if host_conn else None
            if host == player_name:
                return room_name
        return None

    def _create_room(self, conn, payload):
        try:
            player_name = sanitize_name(payload.get("player") or "Jogador")
            senha = sanitize_password(payload.get("password"))
        except ValueError as exc:
            send_message(conn, {"type": "error", "message": str(exc)})
            return

        with self.lock:
            room_name = payload.get("room") or self._waiting_room_for_host(player_name) or self._generate_room_code()
            self.rooms.setdefault(room_name, [])
            if conn not in self.rooms[room_name]:
                self.rooms[room_name].append(conn)
            state = self._ensure_room_state(room_name)
            if conn not in state["order"]:
                state["order"].append(conn)
            if state["current_turn"] is None and state["order"]:
                state["current_turn"] = state["order"][0]
            if senha and not state.get("password"):
                state["password_salt"] = new_salt()
                state["password"] = hash_secret(senha, state["password_salt"])
            self.connections[conn] = {"player": player_name, "room": room_name}

        payload_reply = {
            "type": "room_created",
            "player": player_name,
            "code": room_name,
            "room": room_name,
            "status": "waiting",
            "players": [self.connections[c]["player"] for c in self._room_members(room_name)]
        }
        send_message(conn, payload_reply)
        return payload_reply

    def _start_match(self, conn, payload):
        info = self.connections.get(conn) or {}
        room_name = info.get("room")
        if not room_name or room_name not in self.rooms:
            send_message(conn, {"type": "error", "message": "Voce nao entrou em uma sala."})
            return
        members = self._room_members(room_name)
        if conn not in members:
            send_message(conn, {"type": "error", "message": "Voce nao pertence a esta sala."})
            return
        if members[0] is not conn:
            send_message(conn, {"type": "error", "message": "Somente o anfitriao pode iniciar a partida."})
            return

        state = self._ensure_room_state(room_name)
        if state.get("match") is not None:
            send_message(conn, {"type": "error", "message": "A partida já foi iniciada."})
            return

        player_names = [self.connections[c]["player"] for c in members]
        if len(player_names) < 2:
            send_message(conn, {"type": "error", "message": "É necessário pelo menos dois jogadores para iniciar a partida."})
            return

        escolhas = payload.get("classes") or payload.get("passivas") or {}
        if not isinstance(escolhas, dict):
            escolhas = {}
        jogadores = Jogador.criar_elenco(player_names, escolhas)
        partida = Partida(jogadores)

        state["match"] = partida
        state["shop"] = Equipamento.gerar_estoque(1, 3)
        state["status"] = "started"
        state["players"] = player_names
        state["saved_order"] = player_names
        state["rodada"] = 1
        if state["order"]:
            state["current_turn"] = state["order"][0]
            primeiro = partida.jogadores[0]
            primeiro.iniciar_turno()
            state["saved_current_turn"] = primeiro.nome

        response = {
            "type": "match_started",
            "room": room_name,
            "players": player_names,
            "current_turn": self.connections.get(state["current_turn"], {}).get("player"),
            "status": "started",
            "match": {
                "players": [{"nome": j.nome, "classe": j.classe, "hp": j.hp, "max_hp": j.max_hp} for j in partida.jogadores]
            }
        }

        for client_conn in self._room_members(room_name):
            send_message(client_conn, response)
        return response

    def _broadcast(self, room_name, payload, sender=None):
        for conn in list(self._room_members(room_name)):
            if conn is sender:
                continue
            try:
                send_message(conn, payload)
            except OSError:
                self._remove_connection(conn)

    def _remove_connection(self, conn):
        player_data = self.connections.pop(conn, None)
        if not player_data:
            return

        room_name = player_data.get("room")
        room_state = self.room_state.get(room_name)
        started = bool(room_state and room_state.get("status") == "started")

        if room_name and conn in self._room_members(room_name):
            self.rooms[room_name].remove(conn)
            if not self.rooms[room_name] and not started:
                self.rooms.pop(room_name, None)

        if room_state:
            if room_state.get("current_turn") == conn and player_data.get("player"):
                room_state["saved_current_turn"] = player_data["player"]
            if conn in room_state.get("order", []):
                room_state["order"].remove(conn)
            if room_state.get("current_turn") == conn:
                room_state["current_turn"] = room_state["order"][0] if room_state["order"] else None
            if not room_state.get("order") and not started:
                self.room_state.pop(room_name, None)

    def _handle_join(self, conn, payload):
        room_name = payload.get("room", "default")
        try:
            player_name = sanitize_name(payload.get("player") or "Jogador")
            senha = sanitize_password(payload.get("password"))
        except ValueError as exc:
            send_message(conn, {"type": "error", "message": str(exc)})
            return

        with self.lock:
            state = self._ensure_room_state(room_name)
            if state.get("password") and state["password"] != hash_secret(senha, state.get("password_salt", "")):
                send_message(conn, {"type": "error", "message": "Senha da sala inválida."})
                return
            members = self.rooms.setdefault(room_name, [])
            started = state.get("match") is not None and state.get("status") in {"started", "finished"}
            expected = self._expected_names(state)
            connected = [
                self.connections[c]["player"]
                for c in members
                if c is not conn and c in self.connections
            ]
            if started and player_name not in expected:
                send_message(conn, {
                    "type": "error",
                    "message": "A partida já foi iniciada. Não é possível entrar na sala durante o jogo.",
                })
                return
            if player_name in connected:
                send_message(conn, {
                    "type": "error",
                    "message": f"O jogador {player_name} já existe nesta sala.",
                })
                return
            if conn not in members and len(members) >= self.MAX_PLAYERS:
                send_message(conn, {
                    "type": "error",
                    "message": f"A sala já está cheia (máximo {self.MAX_PLAYERS} jogadores).",
                })
                return

            existing = self.connections.get(conn)
            if existing:
                previous_room = existing.get("room")
                if previous_room and previous_room in self.rooms and previous_room != room_name:
                    if conn in self.rooms[previous_room]:
                        self.rooms[previous_room].remove(conn)
                    if not self.rooms[previous_room]:
                        self.rooms.pop(previous_room, None)

            if conn in members:
                members.remove(conn)
            members.append(conn)

            self.connections[conn] = {"player": player_name, "room": room_name}
            self._rebuild_order(room_name)

        current_turn_player = self.connections.get(
            self.room_state.get(room_name, {}).get("current_turn"),
            {}
        ).get("player")

        send_message(conn, {
            "type": "welcome",
            "status": "ok",
            "player": player_name,
            "room": room_name,
            "current_turn": current_turn_player,
            "players": [self.connections[c]["player"] for c in self._room_members(room_name)]
        })

        self._broadcast(room_name, {
            "type": "player_joined",
            "player": player_name,
            "players": [self.connections[c]["player"] for c in self._room_members(room_name)],
            "current_turn": current_turn_player
        }, sender=conn)

    def _sanitize_action(self, state, action_name):
        if state.get("status") == "finished":
            return False, "A partida ja terminou."
        if not state.get("match"):
            return False, "A partida ainda nao foi iniciada."
        if action_name not in {"attack", "shop", "buy", "equip", "use_magic"}:
            return False, "Acao invalida."
        return True, None

    def _save_room_state(self, room_name):
        state = self.room_state.get(room_name)
        if not state or "match" not in state:
            return
        match = state["match"]
        state["players"] = [
            {"nome": jogador.nome, "classe": jogador.classe, "hp": jogador.hp, "max_hp": jogador.max_hp}
            for jogador in match.jogadores
        ]

    def _attack_action(self, state, conn, payload):
        match = state["match"]
        atacante = next((j for j in match.jogadores if j.nome == payload["player"]), None)
        alvo_nome = payload.get("target")
        alvo = next((j for j in match.jogadores if j.nome == alvo_nome), None)

        if atacante is None or alvo is None or alvo is atacante:
            return {"type": "error", "message": "Alvo invalido."}
        if alvo.hp <= 0:
            return {"type": "error", "message": "O alvo ja esta morto."}

        jogada = resolver_jogada(
            match,
            atacante,
            "attack",
            alvo_nome=alvo_nome,
            rodada=state.get("rodada", 1),
            shop=state.get("shop", []),
        )
        if not jogada.get("ok"):
            return {"type": "error", "message": jogada.get("erro") or "Alvo invalido."}
        resultado = {"acertou": jogada.get("result") == "hit", "dano": jogada.get("damage", 0)}
        resposta = {
            "type": "action",
            "room": payload["room"],
            "player": payload["player"],
            "action": "attack",
            "target": alvo_nome,
            "result": "hit" if resultado["acertou"] else "miss",
            "damage": resultado["dano"],
            "critico": jogada.get("critico", False),
            "eventos": serializar_eventos(match.carimbar(jogada.get("eventos"))),
            "target_hp": alvo.hp,
            "state": self._room_snapshot(payload["room"]),
        }

        match.verificar_mortos()
        match.tentar_proxima_onda()
        if match.fim_partida():
            state["status"] = "finished"
            state["current_turn"] = None
            resposta["winner"] = match.vivos()[0].nome if match.vivos() else None
            resposta["status"] = "finished"
            self._save_room_state(payload["room"])
            self.save_state()
            send_message(conn, {"type": "action_ack", "room": payload["room"], "player": payload["player"], "action": "attack", "next_turn": None, "state": self._room_snapshot(payload["room"]), "result": resposta["result"]})
            self._broadcast(payload["room"], resposta, sender=conn)
            return None

        self._advance_turn(payload["room"])
        resposta["next_turn"] = self.connections.get(self.room_state.get(payload["room"], {}).get("current_turn"), {}).get("player")
        resposta["state"] = self._room_snapshot(payload["room"])
        self._save_room_state(payload["room"])
        self.save_state()

        send_message(conn, {"type": "action_ack", "room": payload["room"], "player": payload["player"], "action": "attack", "next_turn": resposta["next_turn"], "state": resposta["state"], "result": resposta["result"]})
        self._broadcast(payload["room"], resposta, sender=conn)
        return None

    def _shop_action(self, state, conn, payload):
        match = state["match"]
        jogador = next((j for j in match.jogadores if j.nome == payload["player"]), None)
        if jogador is None:
            return {"type": "error", "message": "Jogador nao encontrado."}
        if payload.get("action_type") == "refresh":
            if jogador.moedas < 5:
                return {"type": "error", "message": "Moedas insuficientes."}
            jogador.moedas -= 5
            nivel = match.jogadores[0].nivel if match.jogadores else 1
            state["shop"] = Equipamento.gerar_estoque(nivel, 3)
            return {"type": "shop", "room": payload["room"], "items": [{"nome": item.nome, "valor": item.valor, "tipo": item.tipo, "raridade": item.raridade} for item in state["shop"]]}
        item_index = payload.get("item_index")
        if not isinstance(item_index, int) or not 0 <= item_index < len(state.get("shop", [])):
            return {"type": "error", "message": "Item invalido."}
        item = state["shop"][item_index]
        if jogador.moedas < item.valor:
            return {"type": "error", "message": "Moedas insuficientes."}
        jogador.moedas -= item.valor
        jogador.adicionar_item_inventario(item)
        del state["shop"][item_index]
        self._save_room_state(payload["room"])
        self.save_state()
        return {"type": "shop", "room": payload["room"], "result": "purchase", "item": item.nome, "inventory": [item.nome for item in jogador.inventario]}

    def _inventory_action(self, state, conn, payload):
        match = state["match"]
        jogador = next((j for j in match.jogadores if j.nome == payload["player"]), None)
        if jogador is None:
            return {"type": "error", "message": "Jogador nao encontrado."}
        item_index = payload.get("item_index")
        if item_index is None:
            return {"type": "inventory", "items": [{"nome": item.nome, "tipo": item.tipo} for item in jogador.inventario]}
        if not isinstance(item_index, int) or not 0 <= item_index < len(jogador.inventario):
            return {"type": "error", "message": "Item invalido."}
        item = jogador.inventario[item_index]
        jogador.equipar(item)
        self._save_room_state(payload["room"])
        self.save_state()
        return {"type": "inventory", "result": "equip", "item": item.nome, "player": jogador.nome}

    def _magic_action(self, state, conn, payload):
        match = state["match"]
        jogador = next((j for j in match.jogadores if j.nome == payload["player"]), None)
        alvo_nome = payload.get("target")
        alvo = next((j for j in match.jogadores if j.nome == alvo_nome), None)
        magia = payload.get("magic")
        if jogador is None or alvo is None or not magia:
            return {"type": "error", "message": "Magia invalida."}
        magia_obj = next((item for item in jogador.magias if item.nome.lower() == str(magia).lower()), None)
        if magia_obj is not None and magia_obj.tipo == "cura" and alvo.hp <= 0:
            return {"type": "error", "message": "Nao e possivel curar um jogador eliminado."}
        if magia_obj is not None and magia_obj.tipo == "dano" and alvo.hp <= 0:
            return {"type": "error", "message": "O alvo ja esta morto."}
        resultado = jogador.usar_magia(magia, alvo)
        if not resultado:
            return {"type": "error", "message": "Magia indisponivel."}
        self._save_room_state(payload["room"])
        self.save_state()
        return {"type": "magic", "player": jogador.nome, "target": alvo.nome, "magic": magia, "target_hp": alvo.hp}

    def _conclude_action(self, state, conn, payload, result):
        room_name = payload["room"]
        match = state["match"]
        match.verificar_mortos()
        match.tentar_proxima_onda()
        if match.fim_partida():
            state["status"] = "finished"
            state["current_turn"] = None
            result["status"] = "finished"
            result["winner"] = match.vivos()[0].nome if match.vivos() else None
            result["next_turn"] = None
        else:
            self._advance_turn(room_name)
            result["next_turn"] = self.connections.get(
                self.room_state.get(room_name, {}).get("current_turn"),
                {},
            ).get("player")
        result["current_turn"] = result.get("next_turn")
        result["state"] = self._room_snapshot(room_name)
        self._save_room_state(room_name)
        self.save_state()
        send_message(conn, result)
        if result.get("type") not in {"error"}:
            self._broadcast(room_name, result, sender=conn)
        return result

    def _handle_action(self, conn, payload):
        room_name = self.connections.get(conn, {}).get("room")
        if not room_name:
            send_message(conn, {"type": "error", "message": "Voce nao entrou em uma sala."})
            return

        state = self.room_state.get(room_name)
        if not state or not state.get("match"):
            send_message(conn, {"type": "error", "message": "A partida ainda nao foi iniciada."})
            return
        if state["current_turn"] != conn:
            send_message(conn, {"type": "error", "message": "Nao e sua vez."})
            return

        payload = dict(payload)
        payload["type"] = "action"
        payload["room"] = room_name
        payload["player"] = self.connections.get(conn, {}).get("player")
        action_name = payload.get("action")
        allowed, error = self._sanitize_action(state, action_name)
        if not allowed:
            send_message(conn, {"type": "error", "message": error})
            return

        if action_name == "attack":
            result = self._attack_action(state, conn, payload)
            if result is not None:
                send_message(conn, result)
            return
        if action_name in {"shop", "buy"}:
            result = self._shop_action(state, conn, payload)
            if result.get("type") == "error":
                send_message(conn, result)
                return
            self._conclude_action(state, conn, payload, result)
            return
        if action_name == "equip":
            result = self._inventory_action(state, conn, payload)
            if result.get("type") == "error":
                send_message(conn, result)
                return
            self._conclude_action(state, conn, payload, result)
            return
        if action_name == "use_magic":
            result = self._magic_action(state, conn, payload)
            if result.get("type") == "error":
                send_message(conn, result)
                return
            self._conclude_action(state, conn, payload, result)
            return

        send_message(conn, {"type": "error", "message": "Acao invalida."})

    def _handle_list_rooms(self, conn, payload):
        rooms = {}
        for name, members in self.rooms.items():
            status = self.room_state.get(name, {}).get("status", "waiting")
            if status not in {"waiting", "started", None}:
                continue
            rooms[name] = [self.connections[c]["player"] for c in members]
        send_message(conn, {"type": "rooms", "rooms": rooms})

    def _ensure_state_file(self):
        path = self.state_path.parent
        path.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self.state_path.write_text("{}", encoding="utf-8")

    def save_state(self):
        payload = {
            room: {
                "players": room_data.get("saved_order") or self._expected_names(room_data) or [
                    self.connections.get(conn, {}).get("player")
                    for conn in room_data.get("order", [])
                    if conn in self.connections
                ],
                "status": room_data.get("status", "waiting"),
                "current_turn": room_data.get("saved_current_turn") or self.connections.get(room_data.get("current_turn"), {}).get("player"),
                "winner": room_data.get("winner"),
                "order": room_data.get("saved_order") or [
                    self.connections.get(conn, {}).get("player")
                    for conn in room_data.get("order", [])
                    if conn in self.connections
                ],
                "password": room_data.get("password"),
                "rodada": room_data.get("rodada", 1),
                "match": None,
            }
            for room, room_data in self.room_state.items()
            if room in self.rooms
        }
        for room_name, room in payload.items():
            match = self.room_state[room_name].get("match")
            if match is not None:
                room["match"] = {
                    "players": [{"nome": j.nome, "classe": j.classe, "passiva": getattr(j, "passiva", None), "hp": j.hp, "max_hp": j.max_hp, "moedas": j.moedas, "nivel": j.nivel, "experiencia": j.experiencia, "mana": j.mana, "max_mana": j.max_mana} for j in match.jogadores],
                    "mortos": [j.nome for j in match.mortos],
                }
        self.state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_state(self):
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.state_path.write_text("{}", encoding="utf-8")
            return

        self.rooms = {}
        self.room_state = {}
        for room_name, room_data in data.items():
            saved_order = self._player_names(room_data.get("order") or room_data.get("players") or [])
            self.rooms[room_name] = []
            self.room_state[room_name] = {
                "order": [],
                "current_turn": None,
                "status": room_data.get("status", "waiting"),
                "winner": room_data.get("winner"),
                "match": None,
                "players": saved_order,
                "saved_order": saved_order,
                "saved_current_turn": room_data.get("current_turn"),
                "password": room_data.get("password"),
                "rodada": room_data.get("rodada", 1),
            }
            if room_data.get("match"):
                players = [
                    Jogador.criar(j["nome"], passiva=j.get("passiva") or j.get("classe"))
                    for j in room_data["match"]["players"]
                ]
                for player, saved in zip(players, room_data["match"]["players"]):
                    player.hp = saved["hp"]
                    player.max_hp = saved["max_hp"]
                    player.moedas = saved["moedas"]
                    player.nivel = saved["nivel"]
                    player.experiencia = saved["experiencia"]
                    player.mana = saved.get("mana", player.mana)
                    player.max_mana = saved.get("max_mana", player.max_mana)
                partida = Partida(players)
                partida.mortos = [j for j in players if j.nome in room_data["match"].get("mortos", [])]
                self.room_state[room_name]["match"] = partida
                self.room_state[room_name]["saved_order"] = [jogador.nome for jogador in players]

    def _handle_message(self, conn, payload):
        message_type = payload.get("type")

        if message_type == "create_room":
            self._create_room(conn, payload)
            return

        if message_type == "join":
            self._handle_join(conn, payload)
            return

        if message_type == "list_rooms":
            self._handle_list_rooms(conn, payload)
            return

        if message_type == "start_match":
            self._start_match(conn, payload)
            return

        if message_type == "action":
            self._handle_action(conn, payload)
            return

        send_message(conn, {"type": "error", "message": "Tipo de mensagem desconhecido."})

    def handle_client(self, conn, addr):
        try:
            while True:
                payload = receive_message(conn)
                if payload is None:
                    break
                origem = addr[0] if addr else "desconhecido"
                if payload.get("type") in {"join", "create_room"} and not self.join_limiter.check(origem):
                    send_message(conn, {"type": "error", "message": "Muitas tentativas de entrada. Aguarde um pouco."})
                    continue
                if not self.limiter.check(origem):
                    send_message(conn, {"type": "error", "message": "Muitas mensagens. Tente novamente em instantes."})
                    continue
                self._handle_message(conn, payload)
        except (ConnectionResetError, OSError, ValueError):
            pass
        finally:
            self._remove_connection(conn)
            conn.close()

    def serve_forever(self, host=None, port=None, ready=None):
        host = host or self.host
        port = port or self.port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if host in {"0.0.0.0", "::"}:
                print("Aviso: o servidor está escutando em todas as interfaces. Use só em rede confiável.")
            server_socket.bind((host, port))
            server_socket.listen()
            self.host, self.port = server_socket.getsockname()[:2]
            print(f"Servidor TCP do Arena RPG em {self.host}:{self.port}")
            if ready is not None:
                ready.set()
            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()


if __name__ == "__main__":
    LobbyServer().serve_forever()
