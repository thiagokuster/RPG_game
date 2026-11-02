import argparse
import socket
import threading

from magia import Magia

from .protocol import receive_message, send_message


class GameClient:
    def __init__(self, host="127.0.0.1", port=5000, player="Jogador", room="default"):
        self.host = host
        self.port = port
        self.player = player
        self.room = room
        self.socket = None
        self.connected = False

    def connect(self, join=True):
        self.socket = socket.create_connection((self.host, self.port))
        self.socket.settimeout(5)
        self.connected = True
        if join:
            return self.join_room(self.player, self.room)
        return None

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
        self.connected = False
        self.socket = None

    def receive(self, timeout=5):
        if not self.connected:
            raise RuntimeError("Cliente nao esta conectado.")
        self.socket.settimeout(timeout)
        return receive_message(self.socket)

    def join_room(self, player, room):
        self.player = player
        self.room = room
        if not self.connected:
            self.connect(join=False)
        send_message(self.socket, {"type": "join", "player": self.player, "room": self.room})
        response = receive_message(self.socket)
        print(response)
        return response

    def create_room(self):
        if not self.connected:
            self.connect(join=False)
        send_message(self.socket, {"type": "create_room", "player": self.player})
        response = self.receive()
        if response and response.get("code"):
            self.room = response["code"]
        print(response)
        return response

    def start_match(self, classes):
        if not self.connected:
            raise RuntimeError("Cliente nao esta conectado.")
        send_message(self.socket, {"type": "start_match", "room": self.room, "classes": classes})

    def list_rooms(self):
        if not self.connected:
            raise RuntimeError("Cliente nao esta conectado.")
        send_message(self.socket, {"type": "list_rooms"})

    def send_action(self, action, **kwargs):
        if not self.connected:
            raise RuntimeError("Cliente nao esta conectado.")
        if action == "start_match":
            self.start_match(kwargs.get("classes", {}))
            return
        if action == "list_rooms":
            self.list_rooms()
            return
        if action == "create_room":
            self.create_room()
            return
        payload = {"type": "action", "player": self.player, "room": self.room, "action": action}
        payload.update(kwargs)
        send_message(self.socket, payload)

    def listen_forever(self):
        if not self.connected:
            raise RuntimeError("Cliente nao esta conectado.")

        while True:
            message = receive_message(self.socket)
            if message is None:
                break
            print(message)

    @staticmethod
    def parse_command(command):
        parts = command.strip().split()
        if not parts:
            raise ValueError("Informe um comando.")

        action = parts[0].lower()
        payload = {"action": action}

        if action == "attack":
            if len(parts) < 2:
                raise ValueError("Uso: attack <nome-do-alvo>")
            payload["target"] = parts[1]
            return payload

        if action == "shop":
            payload["action_type"] = parts[1].lower() if len(parts) > 1 else "refresh"
            return payload

        if action in {"buy", "equip"}:
            try:
                payload["item_index"] = int(parts[1])
            except (IndexError, ValueError):
                raise ValueError(f"Uso: {action} <numero-do-item>") from None
            return payload

        if action == "use_magic":
            rest = command.strip()[len(parts[0]):].strip()
            if not rest:
                raise ValueError('Uso: use_magic "Bola de Fogo" Alvo')
            if rest.startswith('"'):
                fim = rest.find('"', 1)
                if fim == -1:
                    raise ValueError('Feche as aspas do nome da magia.')
                payload["magic"] = rest[1:fim]
                leftover = rest[fim + 1:].strip()
                if leftover:
                    payload["target"] = leftover
                return payload
            lower = rest.lower()
            for nome in sorted(Magia.nomes_conhecidos(), key=len, reverse=True):
                if lower.startswith(nome.lower()):
                    payload["magic"] = nome
                    leftover = rest[len(nome):].strip()
                    if leftover:
                        payload["target"] = leftover
                    return payload
            payload["magic"] = parts[1]
            if len(parts) > 2:
                payload["target"] = " ".join(parts[2:])
            return payload

        if action in {"start", "start_match"}:
            if len(parts) < 2:
                raise ValueError("Uso: start Nome:Classe Nome:Classe")
            classes = {}
            for part in parts[1:]:
                if ":" not in part:
                    raise ValueError("Uso: start Nome:Classe Nome:Classe")
                nome, classe = part.split(":", 1)
                classes[nome] = classe
            return {"action": "start_match", "classes": classes}

        if action in {"list", "list_rooms"}:
            return {"action": "list_rooms"}

        if action in {"create", "create_room"}:
            return {"action": "create_room"}

        if action in {"help", "ajuda"}:
            return {"action": "help"}

        raise ValueError("Comando invalido. Use: attack, shop, buy, equip, use_magic, start, list, create ou ajuda.")


def main():
    parser = argparse.ArgumentParser(description="Cliente para o RPG online")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--player", default="Jogador")
    parser.add_argument("--room", default="default")
    args = parser.parse_args()

    client = GameClient(host=args.host, port=args.port, player=args.player, room=args.room)
    client.connect()
    print(f"Conectado em {args.room} como {args.player}.")
    print("Comandos: attack, shop, buy, equip, use_magic, start Nome:Classe, list, create, sair")

    def receiver():
        client.listen_forever()

    thread = threading.Thread(target=receiver, daemon=True)
    thread.start()

    while True:
        command = input("\n> ").strip()
        if not command:
            continue
        if command.lower() in {"sair", "quit", "exit"}:
            break

        try:
            payload = client.parse_command(command)
        except ValueError as error:
            print(error)
            continue

        if payload["action"] == "help":
            print('Comandos: attack <alvo>, shop [refresh], buy <item>, equip <item>, use_magic "Bola de Fogo" <alvo>')
            print("          start Nome:Classe Nome:Classe, list, create, sair")
            continue

        client.send_action(**payload)


if __name__ == "__main__":
    main()
