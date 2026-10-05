from random import randint
from time import sleep

from equipamento import Equipamento
from magia import Magia


class Jogador:
    CLASSES = {
        "Guerreiro": {"hp": 120, "ataque_bonus": 3, "dano_bonus": 3, "armor_class": 16, "magias": []},
        "Mago": {"hp": 70, "ataque_bonus": 1, "dano_bonus": 2, "armor_class": 12, "magias": [Magia.bola_de_fogo(), Magia.cura_leve()]},
        "Arqueiro": {"hp": 90, "ataque_bonus": 3, "dano_bonus": 2, "armor_class": 14, "magias": []},
        "Paladino": {"hp": 110, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 15, "magias": [Magia.cura_leve()]},
        "Clerigo": {"hp": 85, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 13, "magias": [Magia.cura_leve(), Magia.rajada_congelante()]},
    }

    def __init__(self, nome, hp, classe="Guerreiro", nivel=1):
        self.nome = nome
        self.hp = hp
        self.max_hp = hp
        self.danobase = 10
        self.agilidadebase = 0
        self.moedas = 0
        self.inventario = []
        self.classe = classe
        self.nivel = nivel
        self.experiencia = 0
        self.proximo_nivel = 100
        self.armor_class = 12
        self.ataque_bonus = 2
        self.dano_bonus = 2
        self.proficiencia = 2
        self.magias = []
        self.arma: Equipamento = None
        self.anel = None
        self.armadura = None
        self.aplicar_classe(classe)

    @classmethod
    def criar_por_classe(cls, nome, classe, nivel=1):
        config = cls.CLASSES.get(classe, cls.CLASSES["Guerreiro"])
        jogador = cls(nome=nome, hp=config["hp"], classe=classe, nivel=nivel)
        jogador.magias = list(config["magias"])
        return jogador

    def aplicar_classe(self, classe):
        config = self.CLASSES.get(classe, self.CLASSES["Guerreiro"])
        self.classe = classe
        self.max_hp = config["hp"]
        self.hp = self.max_hp
        self.ataque_bonus = config["ataque_bonus"]
        self.dano_bonus = config["dano_bonus"]
        self.armor_class = config["armor_class"]
        self.magias = list(config["magias"])

    def ganhar_experiencia(self, xp):
        self.experiencia += xp
        while self.experiencia >= self.proximo_nivel:
            self.experiencia -= self.proximo_nivel
            self.nivel += 1
            self.proximo_nivel = int(self.proximo_nivel * 1.5)
            self.max_hp += 10
            self.hp = self.max_hp
            self.ataque_bonus += 1
            self.dano_bonus += 1
            self.armor_class += 1
            print(f"{self.nome} subiu para o nivel {self.nivel}!")

    def d10(self):
        print("Rolando dado de ataque...")
        sleep(0.5)
        resultado = randint(1, 10)
        print(resultado)
        return resultado

    def d20(self):
        print("Rolando dado de agilidade...")
        sleep(0.5)
        resultado = randint(1, 20)
        print(resultado)
        return resultado

    def danotot(self, d10, d20):
        danotot = d10
        if self.danobase > 0:
            print(f"+ {self.danobase} de bonus")
            danotot += self.danobase
        if self.arma and self.arma.dano > 0:
            danotot += self.arma.dano
            print(f"+ {self.arma.dano}")
        if self.dano_bonus > 0:
            danotot += self.dano_bonus
            print(f"+ {self.dano_bonus} de dano da classe")
        if d20 >= 20:
            print("ATAQUE ESPECIAL!!!")
            sleep(0.3)
            danotot *= 2
        return danotot

    def usar_magia(self, nome_magia, alvo):
        magia = next((m for m in self.magias if m.nome.lower() == nome_magia.lower()), None)
        if magia is None:
            print(f"{self.nome} nao conhece {nome_magia}.")
            return False
        if magia.tipo == "dano":
            dano = magia.dano + self.dano_bonus
            alvo.hp = max(0, alvo.hp - dano)
            print(f"{self.nome} conjurou {magia.nome} e causou {dano} de dano em {alvo.nome}.")
            return True
        if magia.tipo == "cura":
            cura = magia.cura + self.dano_bonus
            self.hp = min(self.max_hp, self.hp + cura)
            print(f"{self.nome} usou {magia.nome} e recuperou {cura} de HP.")
            return True
        return False

    def adicionar_item_inventario(self, item):
        print(f"{item.nome} foi adicionado no inventario")
        self.inventario.append(item)

    def mostrar_inventario(self):
        if not self.inventario:
            print("Inventario vazio")
            return

        fim = len(self.inventario)
        while True:
            from partida import Partida
            print("=== INVENTARIO ===")
            for i, item in enumerate(self.inventario):
                detalhes = []
                if getattr(item, 'dano', 0):
                    detalhes.append(f"dano {item.dano}")
                if getattr(item, 'agilidade', 0):
                    detalhes.append(f"agilidade {item.agilidade}")
                if getattr(item, 'armadura', 0):
                    detalhes.append(f"armadura {item.armadura}")
                if getattr(item, 'bonus_ataque', 0):
                    detalhes.append(f"+{item.bonus_ataque} ataque")
                print(f"-[{i}] {item.nome} | {item.tipo} | {' | '.join(detalhes) if detalhes else 'sem bonus'}")
            print(f"-[{fim}] Saida")
            if self.arma:
                print(f"Arma equipada : {self.arma.nome}")
            if self.anel:
                print(f"Anel equipado : {self.anel.nome}")
            if self.armadura:
                print(f"Armadura equipada : {self.armadura.nome}")
            if self.magias:
                print("Magias: " + ", ".join(m.nome for m in self.magias))

            opc = Partida.validar_opc(list(range(fim + 1)), "Escolha um item do inventario: ")
            if opc is None or opc == fim:
                return
            item = self.inventario[opc]
            if item.tipo in ["arma", "anel", "armadura"]:
                self.equipar(item)
            else:
                print(f"{item.nome} nao pode ser equipado")
            break

    def equipar(self, item):
        if item not in self.inventario:
            print(f"{item.nome} nao esta no inventario")
            return
        if item.tipo == 'arma':
            if self.arma:
                print(f"Desequipando {self.arma.nome}")
            self.arma = item
            self.ataque_bonus += getattr(item, 'bonus_ataque', 0)
        elif item.tipo == 'armadura':
            if self.armadura:
                print(f"Desequipando {self.armadura.nome}")
            self.armadura = item
            self.armor_class += getattr(item, 'armadura', 0)
        elif item.tipo == 'anel':
            if self.anel:
                print(f"Desequipando {self.anel.nome}")
            self.anel = item
        print(f"{self.nome} equipou {item.nome}")

