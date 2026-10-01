from jogador import Jogador
from time import sleep
from random import randint


class Partida:
    def __init__(self, jogadores: list[Jogador]):
        self.jogadores = jogadores
        self.mortos = []

    @staticmethod
    def cabecalho(titulo: str):
        print("\n" + "=" * 80)
        print(f"{titulo:^80}")
        print("=" * 80)

    @classmethod
    def registrar_jogadores(cls, qj, hp):
        jogadores = []
        for i in range(qj):
            nome = f"Jogador {i + 1}"
            jogadores.append(Jogador(nome, hp))
        return jogadores

    @classmethod
    def menu(cls, jogadores: list[Jogador], jog: Jogador, turno):
        cls.cabecalho("BATALHA DO RPG")
        print(f"{'JOGADOR':<15} | {'HP':>5} | {'MOEDAS':>7}")
        print("-" * 80)
        for j in jogadores:
            status = "VIVO" if j.hp > 0 else "MORTO"
            print(f"{j.nome:<15} | {j.hp:>5} | {j.moedas:>7}  [{status}]")
        print("-" * 80)
        print(f"TURNO: {turno:02} | VEZ DE: {jog.nome} | HP: {jog.hp} | MOEDAS: {jog.moedas}")
        print("-" * 80)
        print("[1] ATACAR      [2] LOJA      [3] INVENTARIO")
        print("-" * 80)
        arma = jog.arma.nome if jog.arma else "Nenhuma"
        print(f"ARMA EQUIPADA: {arma}")
        print("=" * 80)

    def verificar_mortos(self):
        for jogador in list(self.jogadores):
            if jogador.hp <= 0:
                print(f"{jogador.nome} morreu")
                self.mortos.append(jogador)
                self.jogadores.remove(jogador)

    def lista_mortos(self):
        print("Vivos :")
        for jog in self.jogadores:
            print(jog.nome)
        if self.mortos:
            for morto in self.mortos:
                print(morto.nome)

    @classmethod
    def ganhar_moeda(cls, jog: Jogador, rodada):
        moedamax = int(4 + rodada / 4)
        fim = 3
        moeda = randint(1, moedamax)
        chance = randint(1, fim)
        if chance == 1:
            print(f"{jog.nome} ganhou {moeda} moedas!")
            jog.moedas += moeda
            sleep(1.5)

    def fim_partida(self):
        if len(self.jogadores) <= 1:
            if self.jogadores:
                campeao: Jogador = self.jogadores[0]
                if campeao.hp >= 1:
                    print(f"{campeao.nome} venceu a partida!!!")
                else:
                    print("Todos morreram.")
            else:
                print("Todos morreram.")
            return True

        return False

    @classmethod
    def validar_opc(cls, lista=None, mensagem=">", mnsgvazio="lista vazia"):
        if not lista:
            print(mnsgvazio)
            return None
        while True:
            try:
                opc = int(input(mensagem))
                if opc in lista:
                    return opc
                print("Opcao invalida")
            except ValueError:
                print("Digite um valor valido")