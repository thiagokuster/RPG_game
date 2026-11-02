import argparse

from online.server import LobbyServer


def main():
    parser = argparse.ArgumentParser(description="Servidor privado do RPG para uso local ou em rede interna.")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor privado.")
    parser.add_argument("--port", type=int, default=5000, help="Porta do servidor privado.")
    args = parser.parse_args()

    if args.host in {"0.0.0.0", "::"}:
        print("Aviso: o servidor está escutando em todas as interfaces. Use só em rede confiável.")
    print(f"Iniciando servidor privado em {args.host}:{args.port}")
    server = LobbyServer(host=args.host, port=args.port)
    server.serve_forever(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
