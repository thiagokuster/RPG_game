from random import randint
from time import sleep

from equipamento import Equipamento
from magia import Magia


class Jogador:
    CLASSES = {
        "Guerreiro": {
            "hp": 100, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 14, "mana": 0, "sorte": 2,
            "magias": [], "reducao_nativa": 1, "critico": 19, "kit": "arma",
        },
        "Mago": {
            "hp": 100, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 14, "mana": 6, "sorte": 2,
            "magias": [Magia.bola_de_fogo(), Magia.cura_leve()], "mana_por_rodada": 1, "kit": "anel_mana",
        },
        "Arqueiro": {
            "hp": 100, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 14, "mana": 0, "sorte": 2,
            "magias": [], "bonus_acerto": 1, "kit": "anel_sorte",
        },
        "Paladino": {
            "hp": 100, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 14, "mana": 4, "sorte": 2,
            "magias": [Magia.cura_leve()], "cura_fator": 0.5, "cura_e_ataque": True,
        },
        "Clerigo": {
            "hp": 100, "ataque_bonus": 2, "dano_bonus": 2, "armor_class": 14, "mana": 5, "sorte": 2,
            "magias": [Magia.cura_leve(), Magia.rajada_congelante()], "rajada_extra_se_ferido": True,
        },
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
        self.mana = 0
        self.max_mana = 0
        self.magias = []
        self.sorte = 1
        self.reducao_nativa = 0
        self.critico = 20
        self.bonus_acerto = 0
        self.mana_por_rodada = 0
        self.cura_fator = 1
        self.cura_e_ataque = False
        self.rajada_extra_se_ferido = False
        self.kit = None
        self.gasta_turno = True
        self.extra_disponivel = True
        self.arma: Equipamento = None
        self.anel = None
        self.armadura = None
        self.aplicar_classe(classe)

    @classmethod
    def criar_por_classe(cls, nome, classe, nivel=1):
        config = cls.CLASSES.get(classe, cls.CLASSES["Guerreiro"])
        jogador = cls(nome=nome, hp=config["hp"], classe=classe, nivel=nivel)
        jogador.magias = list(config["magias"])
        jogador.aplicar_kit()
        return jogador

    def aplicar_classe(self, classe):
        config = self.CLASSES.get(classe, self.CLASSES["Guerreiro"])
        self.classe = classe
        self.max_hp = config["hp"]
        self.hp = self.max_hp
        self.ataque_bonus = config["ataque_bonus"]
        self.dano_bonus = config["dano_bonus"]
        self.armor_class = config["armor_class"]
        self.max_mana = config.get("mana", 0)
        self.mana = self.max_mana
        self.sorte = config.get("sorte", 2)
        self.magias = list(config["magias"])
        self.reducao_nativa = config.get("reducao_nativa", 0)
        self.critico = config.get("critico", 20)
        self.bonus_acerto = config.get("bonus_acerto", 0)
        self.mana_por_rodada = config.get("mana_por_rodada", 0)
        self.cura_fator = config.get("cura_fator", 1)
        self.cura_e_ataque = config.get("cura_e_ataque", False)
        self.rajada_extra_se_ferido = config.get("rajada_extra_se_ferido", False)
        self.kit = config.get("kit")
        self.gasta_turno = True
        self.extra_disponivel = True

    def aplicar_kit(self):
        if self.kit == "arma":
            item = Equipamento("Espada de Treino", dano=2, tipo="arma", raridade="comum", bonus_ataque=1, valor=0)
        elif self.kit == "anel_mana":
            item = Equipamento("Anel Arcano", tipo="anel", raridade="comum", bonus_mana=1, valor=0)
        elif self.kit == "anel_sorte":
            item = Equipamento("Anel da Sorte", tipo="anel", raridade="comum", bonus_sorte=1, valor=0)
        else:
            return
        self.adicionar_item_inventario(item)
        self.equipar(item)

    def iniciar_turno(self):
        self.extra_disponivel = True
        self.gasta_turno = True

    def inicio_rodada(self):
        if self.hp <= 0 or self.mana_por_rodada <= 0:
            return
        self.mana = min(self.max_mana, self.mana + self.mana_por_rodada)

    @property
    def bonus_ataque_total(self):
        return self.ataque_bonus + self.proficiencia + self.agilidadebase + self.bonus_acerto

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
            if self.max_mana > 0:
                self.max_mana += 1
            self.mana = self.max_mana
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
        if d20 >= getattr(self, "critico", 20):
            print("CRITICO! Dano dobrado.")
            sleep(0.3)
            danotot *= 2
        return danotot

    def usar_magia(self, nome_magia, alvo):
        magia = next((m for m in self.magias if m.nome.lower() == nome_magia.lower()), None)
        if magia is None:
            print(f"{self.nome} nao conhece {nome_magia}.")
            return False
        if self.hp <= 0:
            print(f"{self.nome} nao pode conjurar, pois esta morto.")
            return False
        if alvo is None:
            print("Alvo invalido.")
            return False
        if self.mana < magia.custo:
            print(f"{self.nome} nao tem mana suficiente para {magia.nome} (custo {magia.custo}, mana {self.mana}).")
            return False

        self.mana -= magia.custo
        self.gasta_turno = True
        if magia.tipo == "dano":
            if getattr(alvo, "hp", 0) <= 0:
                self.mana += magia.custo
                print("O alvo ja esta morto.")
                return False
            ferido = getattr(alvo, "max_hp", 0) > 0 and alvo.hp < alvo.max_hp
            bruto = magia.dano + self.dano_bonus
            if hasattr(alvo, "receber_dano"):
                aplicado = alvo.receber_dano(bruto)
                dano = aplicado["dano"]
            else:
                alvo.hp = max(0, alvo.hp - bruto)
                dano = bruto
            if self.rajada_extra_se_ferido and ferido and self.extra_disponivel:
                self.gasta_turno = False
                self.extra_disponivel = False
            print(f"{self.nome} conjurou {magia.nome} e causou {dano} de dano em {alvo.nome}.")
            return True
        if magia.tipo == "cura":
            if getattr(alvo, "hp", 0) <= 0:
                self.mana += magia.custo
                print("O alvo ja esta morto.")
                return False
            cura = int((magia.cura + self.dano_bonus) * getattr(self, "cura_fator", 1))
            alvo.hp = min(alvo.max_hp, alvo.hp + cura)
            if self.cura_e_ataque and self.extra_disponivel:
                self.gasta_turno = False
                self.extra_disponivel = False
            print(f"{self.nome} usou {magia.nome} e recuperou {cura} de HP de {alvo.nome}.")
            return True
        self.mana += magia.custo
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
                    detalhes.append(f"CA +{item.armadura}")
                if getattr(item, "reducao", 0):
                    detalhes.append(f"redução {item.reducao}")
                if getattr(item, "durabilidade", 0):
                    detalhes.append(f"durabilidade {item.durabilidade}/{getattr(item, 'max_durabilidade', item.durabilidade)}")
                if getattr(item, 'bonus_ataque', 0):
                    detalhes.append(f"+{item.bonus_ataque} ataque")
                print(f"-[{i}] {item.nome} | {item.tipo} | {' | '.join(detalhes) if detalhes else 'sem bonus'}")
            print(f"-[{fim}] Saida")
            if self.arma:
                print(f"Arma equipada : {self.arma.nome}")
            if self.anel:
                print(f"Anel equipado : {self.anel.nome}")
            if self.armadura:
                print(
                    f"Armadura equipada : {self.armadura.nome} "
                    f"(redução {getattr(self.armadura, 'reducao', 0)}, "
                    f"durabilidade {getattr(self.armadura, 'durabilidade', 0)})"
                )
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

    def _desaplicar_item(self, item):
        if item is None:
            return
        if item.tipo == "arma":
            self.ataque_bonus -= getattr(item, "bonus_ataque", 0)
        elif item.tipo == "armadura":
            self.armor_class -= getattr(item, "armadura", 0)
        elif item.tipo == "anel":
            bonus = getattr(item, "agilidade", 0)
            self.agilidadebase -= bonus
            self.armor_class -= bonus
            self.sorte -= getattr(item, "bonus_sorte", 0)
            self.max_mana -= getattr(item, "bonus_mana", 0)
            self.mana = min(self.mana, self.max_mana)

    def equipar(self, item):
        if item not in self.inventario:
            print(f"{item.nome} nao esta no inventario")
            return False
        if item.tipo == "arma":
            if self.arma is item:
                print(f"{item.nome} ja esta equipada")
                return True
            if self.arma:
                print(f"Desequipando {self.arma.nome}")
                self._desaplicar_item(self.arma)
            self.arma = item
            self.ataque_bonus += getattr(item, "bonus_ataque", 0)
        elif item.tipo == "armadura":
            if self.armadura is item:
                print(f"{item.nome} ja esta equipada")
                return True
            if self.armadura:
                print(f"Desequipando {self.armadura.nome}")
                self._desaplicar_item(self.armadura)
            self.armadura = item
            self.armor_class += getattr(item, "armadura", 0)
        elif item.tipo == "anel":
            if self.anel is item:
                print(f"{item.nome} ja esta equipado")
                return True
            if self.anel:
                print(f"Desequipando {self.anel.nome}")
                self._desaplicar_item(self.anel)
            self.anel = item
            bonus = getattr(item, "agilidade", 0)
            self.agilidadebase += bonus
            self.armor_class += bonus
            self.sorte += getattr(item, "bonus_sorte", 0)
            self.max_mana += getattr(item, "bonus_mana", 0)
            self.mana += getattr(item, "bonus_mana", 0)
        else:
            print(f"{item.nome} nao pode ser equipado")
            return False
        print(f"{self.nome} equipou {item.nome}")
        return True

    def _quebrar_armadura(self):
        item = self.armadura
        if item is None:
            return
        print(f"A armadura {item.nome} de {self.nome} quebrou!")
        self._desaplicar_item(item)
        self.armadura = None
        if item in self.inventario:
            self.inventario.remove(item)

    def receber_dano(self, dano):
        dano = max(0, int(dano))
        reduzido = 0
        quebrou = False
        nativa = max(0, int(getattr(self, "reducao_nativa", 0)))
        if self.armadura and dano > 0:
            armadura = max(0, int(getattr(self.armadura, "reducao", 0)))
            reduzido = min(dano, armadura + nativa)
            desgaste = max(1, min(reduzido, armadura) if armadura else 1)
            self.armadura.durabilidade = max(0, int(getattr(self.armadura, "durabilidade", 0)) - desgaste)
            if self.armadura.durabilidade <= 0:
                quebrou = True
                self._quebrar_armadura()
        elif dano > 0:
            reduzido = min(dano, nativa)
        aplicado = max(0, dano - reduzido)
        self.hp = max(0, self.hp - aplicado)
        return {"dano": aplicado, "reduzido": reduzido, "quebrou": quebrou, "bruto": dano}
