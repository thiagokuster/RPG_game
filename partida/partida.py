from random import randint
from time import sleep

from jogador import Jogador
from monstro import Monstro


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
    def selecionar_classe(cls, numero_jogador):
        classes = ["Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo"]
        print(f"Escolha a classe do Jogador {numero_jogador}:")
        for indice, nome in enumerate(classes, start=1):
            print(f"[{indice}] {nome}")
        while True:
            try:
                escolha = int(input("Classe: "))
                if 1 <= escolha <= len(classes):
                    return classes[escolha - 1]
                print("Opcao invalida")
            except ValueError:
                print("Digite um valor valido")

    @classmethod
    def registrar_jogadores(cls, qj, hp):
        jogadores = []
        for i in range(qj):
            nome = f"Jogador {i + 1}"
            classe = cls.selecionar_classe(i + 1)
            jogadores.append(Jogador.criar_por_classe(nome, classe))
        return jogadores

    @classmethod
    def menu(cls, jogadores: list[Jogador], jog: Jogador, turno):
        cls.cabecalho("BATALHA DO RPG")
        print(f"{'JOGADOR':<15} | {'HP':>5} | {'MOEDAS':>7} | {'CA':>4} | {'NIVEL':>5}")
        print("-" * 90)
        for j in jogadores:
            status = "VIVO" if j.hp > 0 else "MORTO"
            print(f"{j.nome:<15} | {j.hp:>5} | {j.moedas:>7} | {j.armor_class:>4} | {j.nivel:>5}  [{status}]")
        print("-" * 90)
        print(f"TURNO: {turno:02} | VEZ DE: {jog.nome} | CLASSE: {jog.classe} | HP: {jog.hp} | MOEDAS: {jog.moedas} | CA: {jog.armor_class} | NIVEL: {jog.nivel}")
        print("-" * 90)
        print("[1] ATACAR      [2] LOJA      [3] INVENTARIO")
        print("-" * 90)
        arma = jog.arma.nome if jog.arma else "Nenhuma"
        armadura = jog.armadura.nome if jog.armadura else "Nenhuma"
        print(f"ARMA EQUIPADA: {arma}")
        print(f"ARMADURA: {armadura}")
        print(f"BONUS DE ATAQUE: +{jog.ataque_bonus + jog.proficiencia}")
        if jog.magias:
            print("MAGIAS: " + ", ".join(m.nome for m in jog.magias))
        print("=" * 90)

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
        moeda = randint(1, moedamax)
        chance = randint(1, 3)
        if chance == 1:
            print(f"{jog.nome} ganhou {moeda} moedas!")
            jog.moedas += moeda
            sleep(1.5)
            jog.ganhar_experiencia(10)

    def gerar_evento_monstro(self, rodada):
        if rodada <= 2:
            chance = 1
        elif rodada <= 5:
            chance = 2
        elif rodada <= 10:
            chance = 3
        else:
            chance = 4

        chance += max(0, (rodada - 1) // 10)
        if randint(1, 100) <= chance:
            nivel = max(1, (rodada // 2) + 1)
            monstro = Monstro.gerar_monstro(nivel)
            print(f"Evento aleatorio! Um {monstro.nome} apareceu na rodada {rodada}.")
            return monstro
        return None

    def resolver_evento_monstro(self, jogador, monstro):
        print(f"{jogador.nome} foi surpreendido por {monstro.nome}!")
        while monstro.hp > 0 and jogador.hp > 0:
            ataque = jogador.d20() + jogador.ataque_bonus + jogador.proficiencia
            if ataque >= monstro.armor_class:
                dano = jogador.d10() + jogador.dano_bonus + (jogador.arma.dano if jogador.arma else 0)
                if jogador.arma and jogador.arma.bonus_ataque:
                    dano += jogador.arma.bonus_ataque
                monstro.hp -= dano
                print(f"{jogador.nome} atacou {monstro.nome} e causou {dano} de dano.")
            else:
                print(f"{jogador.nome} errou o ataque contra {monstro.nome}.")
            if monstro.hp <= 0:
                break
            monstro.atacar(jogador)
            if jogador.hp <= 0:
                break

        if monstro.hp <= 0:
            print(f"{monstro.nome} foi derrotado!")
            jogador.moedas += monstro.recompensa
            jogador.ganhar_experiencia(monstro.xp)
            return True
        print(f"{jogador.nome} foi derrotado por {monstro.nome}.")
        return False

    def fim_partida(self):
        if len(self.jogadores) == 0:
            print("Todos morreram. Nao houve vencedor.")
            return True

        if len(self.jogadores) == 1:
            campeao: Jogador = self.jogadores[0]
            if campeao.hp >= 1:
                print(f"{campeao.nome} venceu a partida!!!")
            else:
                print("Todos morreram. Nao houve vencedor.")
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