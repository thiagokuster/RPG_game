from random import randint

from equipamento import Equipamento
from magia import Magia
from motor.eventos import evento, nome


class Jogador:
    BASE = {
        "hp": 100,
        "ataque_bonus": 2,
        "dano_bonus": 2,
        "armor_class": 14,
        "mana": 4,
        "sorte": 2,
        "kit": "arma",
    }
    PASSIVAS = ("Bruto", "Arcano", "Preciso")
    _ALIASES_PASSIVA = {
        "bruto": "Bruto",
        "ferro": "Bruto",
        "guerreiro": "Bruto",
        "paladino": "Bruto",
        "arcano": "Arcano",
        "mago": "Arcano",
        "clerigo": "Arcano",
        "preciso": "Preciso",
        "arqueiro": "Preciso",
    }

    def __init__(self, nome, hp=100, classe="Aventureiro", nivel=1):
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
        self.kit = None
        self.gasta_turno = True
        self.extra_disponivel = True
        self.arma: Equipamento = None
        self.anel = None
        self.armadura = None
        self.passiva = "Bruto"
        self.aplicar_base()

    @classmethod
    def passiva_conhecida(cls, valor):
        if not valor:
            return None
        chave = str(valor).strip().lower()
        if chave in cls._ALIASES_PASSIVA:
            return cls._ALIASES_PASSIVA[chave]
        for item in cls.PASSIVAS:
            if item.lower() == chave:
                return item
        return None

    @classmethod
    def normalizar_passiva(cls, valor, padrao=None):
        return cls.passiva_conhecida(valor) or padrao or "Bruto"

    @classmethod
    def criar(cls, nome, nivel=1, passiva=None):
        jogador = cls(nome=nome, hp=cls.BASE["hp"], classe="Aventureiro", nivel=nivel)
        jogador.aplicar_passiva(passiva)
        jogador.aplicar_kit()
        return jogador

    @classmethod
    def criar_elenco(cls, nomes, passivas=None):
        if not isinstance(passivas, dict):
            passivas = {}
        elenco = []
        for indice, personagem in enumerate(nomes):
            padrao = cls.PASSIVAS[indice % 3]
            escolhida = cls.passiva_conhecida(passivas.get(personagem))
            elenco.append(cls.criar(personagem, passiva=escolhida or padrao))
        return elenco

    @classmethod
    def criar_por_classe(cls, nome, classe=None, nivel=1):
        return cls.criar(nome, nivel=nivel, passiva=classe)

    def aplicar_base(self):
        config = self.BASE
        self.classe = "Aventureiro"
        self.max_hp = config["hp"]
        self.hp = self.max_hp
        self.ataque_bonus = config["ataque_bonus"]
        self.dano_bonus = config["dano_bonus"]
        self.armor_class = config["armor_class"]
        self.max_mana = config.get("mana", 0)
        self.mana = self.max_mana
        self.sorte = config.get("sorte", 2)
        self.magias = [Magia.cura_leve()]
        self.reducao_nativa = 0
        self.critico = 20
        self.bonus_acerto = 0
        self.mana_por_rodada = 0
        self.kit = config.get("kit")
        self.gasta_turno = True
        self.extra_disponivel = True

    def aplicar_passiva(self, passiva=None):
        self.aplicar_base()
        nome = self.normalizar_passiva(passiva)
        self.passiva = nome
        if nome == "Bruto":
            self.max_hp = 115
            self.hp = self.max_hp
            self.max_mana = 3
            self.mana = 3
            self.reducao_nativa = 1
            self.magias = [Magia.cura_leve(), Magia.golpe_de_energia()]
        elif nome == "Arcano":
            self.max_hp = 90
            self.hp = self.max_hp
            self.max_mana = 6
            self.mana = 6
            self.mana_por_rodada = 1
            self.kit = "anel_mana"
            self.magias = [Magia.cura_leve(), Magia.bola_de_fogo()]
        else:
            self.bonus_acerto = 1
            self.critico = 19
            self.kit = "anel_sorte"
            self.magias = [Magia.cura_leve(), Magia.rajada_congelante()]

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
        eventos = []
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
            if self.nivel >= 3:
                self._desbloquear_magias()
            eventos.append(evento("nivel", de=self.nome, nivel=self.nivel, passiva=self.passiva))
        return eventos

    def _desbloquear_magias(self):
        conhecidas = {magia.nome for magia in self.magias}
        extras = [Magia.bola_de_fogo(), Magia.rajada_congelante(), Magia.golpe_de_energia()]
        for magia in extras:
            if magia.nome not in conhecidas:
                self.magias.append(magia)
                conhecidas.add(magia.nome)

    def d10(self):
        return randint(1, 10)

    def d20(self):
        return randint(1, 20)

    def danotot(self, d10, d20):
        danotot = d10
        if self.danobase > 0:
            danotot += self.danobase
        if self.arma and self.arma.dano > 0:
            danotot += self.arma.dano
        if self.dano_bonus > 0:
            danotot += self.dano_bonus
        if d20 >= getattr(self, "critico", 20):
            danotot *= 2
        return danotot

    def usar_magia(self, nome_magia, alvo):
        magia = next((m for m in self.magias if m.nome.lower() == nome_magia.lower()), None)
        if magia is None or self.hp <= 0 or alvo is None:
            return False
        if self.mana < magia.custo:
            return False

        self.mana -= magia.custo
        self.gasta_turno = True
        if magia.tipo == "dano":
            if getattr(alvo, "hp", 0) <= 0:
                self.mana += magia.custo
                return False
            bruto = magia.dano + self.dano_bonus
            if hasattr(alvo, "receber_dano"):
                aplicado = alvo.receber_dano(bruto)
                dano = aplicado["dano"]
            else:
                alvo.hp = max(0, alvo.hp - bruto)
                dano = bruto
            eventos = [evento("magia", de=self.nome, para=nome(alvo), magia=magia.nome, dano=dano, cura=0, critico=False)]
            if getattr(alvo, "hp", 0) <= 0:
                eventos.append(evento("morte", de=nome(alvo)))
            return evento("magia", de=self.nome, para=nome(alvo), magia=magia.nome, dano=dano, cura=0, ok=True, eventos=eventos)
        if magia.tipo == "cura":
            if getattr(alvo, "hp", 0) <= 0:
                self.mana += magia.custo
                return False
            cura = magia.cura + self.dano_bonus
            alvo.hp = min(alvo.max_hp, alvo.hp + cura)
            return evento(
                "magia",
                de=self.nome,
                para=nome(alvo),
                magia=magia.nome,
                dano=0,
                cura=cura,
                ok=True,
                eventos=[evento("magia", de=self.nome, para=nome(alvo), magia=magia.nome, dano=0, cura=cura)],
            )
        self.mana += magia.custo
        return False

    def adicionar_item_inventario(self, item):
        self.inventario.append(item)
        return evento("item", de=self.nome, item=item.nome)

    def detalhes_item(self, item):
        detalhes = []
        if getattr(item, "dano", 0):
            detalhes.append(f"dano {item.dano}")
        if getattr(item, "agilidade", 0):
            detalhes.append(f"agilidade {item.agilidade}")
        if getattr(item, "armadura", 0):
            detalhes.append(f"CA +{item.armadura}")
        if getattr(item, "reducao", 0):
            detalhes.append(f"redução {item.reducao}")
        if getattr(item, "durabilidade", 0):
            detalhes.append(f"durabilidade {item.durabilidade}/{getattr(item, 'max_durabilidade', item.durabilidade)}")
        if getattr(item, "bonus_ataque", 0):
            detalhes.append(f"+{item.bonus_ataque} ataque")
        return detalhes

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
            return False
        if item.tipo == "arma":
            if self.arma is item:
                return True
            if self.arma:
                self._desaplicar_item(self.arma)
            self.arma = item
            self.ataque_bonus += getattr(item, "bonus_ataque", 0)
        elif item.tipo == "armadura":
            if self.armadura is item:
                return True
            if self.armadura:
                self._desaplicar_item(self.armadura)
            self.armadura = item
            self.armor_class += getattr(item, "armadura", 0)
        elif item.tipo == "anel":
            if self.anel is item:
                return True
            if self.anel:
                self._desaplicar_item(self.anel)
            self.anel = item
            bonus = getattr(item, "agilidade", 0)
            self.agilidadebase += bonus
            self.armor_class += bonus
            self.sorte += getattr(item, "bonus_sorte", 0)
            self.max_mana += getattr(item, "bonus_mana", 0)
            self.mana += getattr(item, "bonus_mana", 0)
        else:
            return False
        return True

    def _quebrar_armadura(self):
        item = self.armadura
        if item is None:
            return
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
