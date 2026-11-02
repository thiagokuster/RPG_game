from random import choice, choices, randint


QUALIDADE = {
    "comum": 0.5,
    "raro": 0.6,
    "epico": 1.1,
    "lendario": 1.7,
    "mitico": 2,
}

PESOS_RARIDADE = [70, 20, 9, 2, 0.5]

NOMES = {
    "arma": {
        "comum": ["Faca", "Adaga", "Clava", "Porrete"],
        "raro": ["Espada Curta", "Machado", "Lança", "Foice"],
        "epico": ["Katana", "Espada do Guardião", "Machado Rúnico"],
        "lendario": ["Gume Ancestral", "Lança do Crepúsculo"],
        "mitico": ["Lâmina Primordial", "Martelo do Éter"],
    },
    "armadura": {
        "comum": ["Gibão Usado", "Peitoral Simples", "Cota Velha"],
        "raro": ["Cota de Malha", "Peitoral do Valor", "Armadura Leve"],
        "epico": ["Armadura Pesada", "Couraça Rúnica", "Escudo de Guerra"],
        "lendario": ["Couraça Ancestral", "Baluarte do Guardião"],
        "mitico": ["Égide Primordial", "Carapaça do Éter"],
    },
    "anel": {
        "comum": ["Anel Simples", "Pingente de Cobre"],
        "raro": ["Amuleto do Valor", "Anel da Esquiva"],
        "epico": ["Selo Rúnico", "Talismã da Sorte"],
        "lendario": ["Anel Ancestral", "Olho do Crepúsculo"],
        "mitico": ["Selo Primordial", "Amuleto do Éter"],
    },
}


class Equipamento:
    def __init__(
        self,
        nome,
        dano=0,
        valor=0,
        agilidade=0,
        tipo=None,
        raridade=None,
        bonus_ataque=0,
        armadura=0,
        reducao=None,
        durabilidade=None,
        bonus_mana=0,
        bonus_sorte=0,
    ):
        self.nome = nome
        self.dano = dano
        self.valor = valor
        self.agilidade = agilidade
        self.tipo = tipo
        self.raridade = raridade
        self.bonus_ataque = bonus_ataque
        self.armadura = armadura
        if reducao is None:
            reducao = armadura if tipo == "armadura" else 0
        self.reducao = max(0, int(reducao))
        if durabilidade is None:
            durabilidade = 12 if tipo == "armadura" else 0
        self.durabilidade = max(0, int(durabilidade))
        self.max_durabilidade = self.durabilidade
        self.bonus_mana = max(0, int(bonus_mana or 0))
        self.bonus_sorte = max(0, int(bonus_sorte or 0))

    def descricao(self):
        partes = [self.nome]
        if self.raridade:
            partes.append(self.raridade)
        if self.tipo == "arma":
            partes.append(f"dano {self.dano}")
            if self.bonus_ataque:
                partes.append(f"+{self.bonus_ataque} ataque")
        elif self.tipo == "armadura":
            partes.append(f"CA +{self.armadura}")
            partes.append(f"redução {self.reducao}")
            partes.append(f"durabilidade {self.durabilidade}/{self.max_durabilidade}")
        elif self.tipo == "anel":
            if self.agilidade:
                partes.append(f"agilidade {self.agilidade}")
        partes.append(f"{self.valor} moedas")
        return " | ".join(partes)

    @staticmethod
    def _escolher_raridade():
        return choices(list(QUALIDADE.keys()), weights=PESOS_RARIDADE, k=1)[0]

    @classmethod
    def _nome_por_raridade(cls, tipo, raridade):
        tabela = NOMES.get(tipo, {})
        opcoes = tabela.get(raridade) or tabela.get("comum") or ["Item"]
        return choice(opcoes)

    @classmethod
    def gerar_por_categoria(cls, turno, tipo="arma"):
        turno = max(1, int(turno or 1))
        if tipo == "acessorio":
            tipo = "anel"
        if tipo not in {"arma", "armadura", "anel"}:
            tipo = "arma"
        raridade = cls._escolher_raridade()
        qualidade = QUALIDADE[raridade]
        nome = cls._nome_por_raridade(tipo, raridade)

        if tipo == "arma":
            dano_max = max(1, int(qualidade * turno))
            dano_min = 1
            if raridade == "epico":
                dano_min = max(1, int(dano_max * 0.25))
            elif raridade == "lendario":
                dano_min = max(1, int(dano_max * 0.50))
            elif raridade == "mitico":
                dano_min = max(1, int(dano_max * 0.80))
            if dano_min > dano_max:
                dano_min = dano_max
            dano = randint(dano_min, dano_max)
            bonus_ataque = max(0, int(qualidade * 2))
            return cls(
                nome=nome,
                dano=dano,
                valor=max(1, int(dano * 0.7) + bonus_ataque),
                tipo="arma",
                raridade=raridade,
                bonus_ataque=bonus_ataque,
            )

        if tipo == "armadura":
            armadura = 1 + int(qualidade * 2)
            reducao = armadura
            durabilidade = 8 + int(qualidade * 10)
            return cls(
                nome=nome,
                valor=max(1, int(armadura * 3)),
                tipo="armadura",
                raridade=raridade,
                armadura=armadura,
                reducao=reducao,
                durabilidade=durabilidade,
            )

        agilidade = 1 if raridade in {"comum", "raro"} else 2
        return cls(
            nome=nome,
            valor=max(1, int(turno * (1 + qualidade))),
            agilidade=agilidade,
            tipo="anel",
            raridade=raridade,
        )

    @classmethod
    def gerarEquipamento(cls, turno):
        return cls.gerar_por_categoria(turno, choice(["arma", "armadura", "anel"]))

    @classmethod
    def gerar_estoque(cls, turno, slots=3):
        categorias = ["arma", "armadura", "anel"]
        estoque = []
        for indice in range(max(1, int(slots))):
            tipo = categorias[indice] if indice < len(categorias) else choice(categorias)
            estoque.append(cls.gerar_por_categoria(turno, tipo))
        return estoque
