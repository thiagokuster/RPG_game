from random import randint
from time import sleep

from combate import resolver_ataque
from eventos import gerar_evento, resolver_evento
from jogador import Jogador
from monstro import Monstro


class Partida:
    def __init__(self, jogadores: list[Jogador]):
        self.jogadores = jogadores
        self.mortos = []

    def vivos(self):
        return [jogador for jogador in self.jogadores if jogador.hp > 0]

    def proximo_vivo(self, atual):
        vivos = self.vivos()
        if len(vivos) <= 1:
            return None
        if atual not in self.jogadores:
            return vivos[0]
        indice = self.jogadores.index(atual)
        total = len(self.jogadores)
        for passo in range(1, total + 1):
            candidato = self.jogadores[(indice + passo) % total]
            if candidato.hp > 0:
                return candidato
        return None

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
        print(f"{'JOGADOR':<15} | {'HP':>5} | {'MOEDAS':>7} | {'CA':>4} | {'NIVEL':>5} | {'MANA':>5}")
        print("-" * 90)
        for j in jogadores:
            status = "VIVO" if j.hp > 0 else "MORTO"
            print(f"{j.nome:<15} | {j.hp:>5} | {j.moedas:>7} | {j.armor_class:>4} | {j.nivel:>5} | {j.mana:>5}  [{status}]")
        print("-" * 90)
        print(
            f"TURNO: {turno:02} | VEZ DE: {jog.nome} | CLASSE: {jog.classe} | "
            f"HP: {jog.hp} | MOEDAS: {jog.moedas} | CA: {jog.armor_class} | "
            f"NIVEL: {jog.nivel} | MANA: {jog.mana}/{jog.max_mana}"
        )
        print("-" * 90)
        print("[1] ATACAR      [2] LOJA      [3] INVENTARIO      [4] MAGIA")
        print("-" * 90)
        arma = jog.arma.nome if jog.arma else "Nenhuma"
        armadura = jog.armadura.nome if jog.armadura else "Nenhuma"
        print(f"ARMA EQUIPADA: {arma}")
        if jog.armadura:
            print(
                f"ARMADURA: {armadura} | redução {getattr(jog.armadura, 'reducao', 0)} | "
                f"durabilidade {getattr(jog.armadura, 'durabilidade', 0)}"
            )
        else:
            print(f"ARMADURA: {armadura}")
        print(f"SORTE: {getattr(jog, 'sorte', 1)}")
        print(f"BONUS DE ATAQUE: +{jog.bonus_ataque_total}")
        if jog.magias:
            print("MAGIAS: " + ", ".join(f"{m.nome} ({m.custo} mana)" for m in jog.magias))
        print("=" * 90)

    def verificar_mortos(self):
        for jogador in self.jogadores:
            if jogador.hp <= 0 and jogador not in self.mortos:
                print(f"{jogador.nome} morreu")
                self.mortos.append(jogador)

    def lista_mortos(self):
        print("Vivos :")
        for jog in self.vivos():
            print(jog.nome)
        if self.mortos:
            print("Mortos :")
            for morto in self.mortos:
                print(morto.nome)

    @classmethod
    def ganhar_moeda(cls, jog: Jogador, rodada, silencioso=False):
        moedamax = int(4 + rodada / 4)
        moeda = randint(1, moedamax)
        chance = randint(1, 3)
        if chance == 1:
            if not silencioso:
                print(f"{jog.nome} ganhou {moeda} moedas!")
            jog.moedas += moeda
            if not silencioso:
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

    def iniciar_rodada(self):
        for jogador in self.vivos():
            jogador.inicio_rodada()

    def gerar_evento_aleatorio(self, rodada, jogador=None):
        return gerar_evento(rodada, jogador)

    def resolver_evento_aleatorio(self, jogador, evento, rodada=1):
        if not evento:
            return None
        if evento.get("tipo") == "monstro":
            return self.resolver_evento_monstro(jogador, evento["monstro"])
        return resolver_evento(jogador, evento, rodada)

    def resolver_evento_monstro(self, jogador, monstro):
        print(f"{jogador.nome} foi surpreendido por {monstro.nome}!")
        while monstro.hp > 0 and jogador.hp > 0:
            resultado = resolver_ataque(jogador, monstro)
            if not resultado["acertou"] and resultado.get("motivo") != "erro":
                break
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

    def escolher_e_usar_magia(self, jog):
        if not jog.magias:
            print("Voce nao conhece magias.")
            return None
        print("Magias:")
        for i, magia in enumerate(jog.magias):
            print(f"- [{i}] {magia.nome} ({magia.tipo}, custo {magia.custo})")
        print("- [-1] Voltar")
        opc = self.validar_opc(list(range(len(jog.magias))) + [-1], "Magia: ")
        if opc is None or opc == -1:
            return None
        magia = jog.magias[opc]
        if magia.tipo == "cura":
            alvos = [alvo for alvo in self.jogadores if alvo.hp > 0]
        else:
            alvos = [alvo for alvo in self.jogadores if alvo is not jog and alvo.hp > 0]
        if not alvos:
            print("Nenhum alvo disponivel.")
            return False
        if len(alvos) == 1:
            alvo = alvos[0]
        else:
            for i, alvo in enumerate(alvos):
                print(f"- [{i}] {alvo.nome} HP {alvo.hp}")
            indice = self.validar_opc(list(range(len(alvos))), "Alvo: ")
            if indice is None:
                return None
            alvo = alvos[indice]
        return jog.usar_magia(magia.nome, alvo)

    def fim_partida(self):
        vivos = self.vivos()
        if len(vivos) == 0:
            print("Todos morreram. Nao houve vencedor.")
            return True

        if len(vivos) == 1:
            campeao: Jogador = vivos[0]
            print(f"{campeao.nome} venceu a partida!!!")
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
