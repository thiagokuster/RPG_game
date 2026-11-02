import argparse
import threading

from online.client import GameClient


def main():
    parser = argparse.ArgumentParser(description="Cliente privado para entrar na sala do RPG em ambiente local.")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor privado.")
    parser.add_argument("--port", type=int, default=5000, help="Porta do servidor privado.")
    parser.add_argument("--player", default="Jogador", help="Nome do jogador.")
    parser.add_argument("--room", default="Sala1", help="Código ou nome da sala.")
    args = parser.parse_args()

    client = GameClient(host=args.host, port=args.port, player=args.player, room=args.room)
    client.connect()
    print(f"Conectado em {args.room} como {args.player}.")
    print("Comandos: attack, shop, buy, equip, use_magic, start Nome:Classe, list, create, ajuda, sair")

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
