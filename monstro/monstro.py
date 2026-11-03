from random import choice, randint

from motor.eventos import evento, nome


class Monstro:
    def __init__(self, nome, hp, ataque_bonus, armor_class, dano, xp=25, recompensa=10, tipo="bestia"):
        self.nome = nome
        self.hp = hp
        self.max_hp = hp
        self.ataque_bonus = ataque_bonus
        self.armor_class = armor_class
        self.dano = dano
        self.xp = xp
        self.recompensa = recompensa
        self.tipo = tipo
        self.classe = tipo
        self.mana = 0
        self.max_mana = 0
        self.critico = 20
        self.bonus_ataque_total = ataque_bonus

    @classmethod
    def gerar_monstro(cls, nivel=1):
        fichas = [
            ("Goblin", 18, 3, 12, 5, 20, 8, "humanoide"),
            ("Esqueleto", 24, 4, 13, 7, 25, 12, "undead"),
            ("Lobo Selvagem", 30, 5, 13, 8, 30, 15, "bestia"),
            ("Orc", 42, 6, 14, 10, 40, 18, "humanoide"),
            ("Manticora", 55, 7, 15, 12, 55, 22, "monstro"),
        ]

        nivel_ajustado = max(1, min(nivel, len(fichas)))
        escolha = fichas[min(len(fichas) - 1, nivel_ajustado - 1)]
        nome_monstro, hp, ataque_bonus, armor_class, dano, xp, recompensa, tipo = escolha

        if nivel >= 4:
            nome_monstro = choice([nome_monstro, "Bandido da Selva", "Basilisco Pequeno", "Rastejador"])
            hp += 15
            ataque_bonus += 1
            dano += 2
            recompensa += 10

        return cls(nome_monstro, hp, ataque_bonus, armor_class, dano, xp, recompensa, tipo)

    @classmethod
    def gerar_chefe(cls, onda=1):
        hp = 40 + onda * 18
        return cls(
            nome=f"Chefe da onda {onda}",
            hp=hp,
            ataque_bonus=4 + onda,
            armor_class=13 + min(4, onda),
            dano=8 + onda,
            xp=40 + onda * 15,
            recompensa=20 + onda * 8,
            tipo="chefe",
        )

    def atacar(self, alvo):
        ataque = randint(1, 20) + self.ataque_bonus
        if ataque >= getattr(alvo, "armor_class", 12):
            bruto = randint(1, self.dano) + max(1, self.ataque_bonus // 2)
            if hasattr(alvo, "receber_dano"):
                aplicado = alvo.receber_dano(bruto)
                dano = aplicado["dano"]
            else:
                alvo.hp = max(0, getattr(alvo, "hp", 0) - bruto)
                dano = bruto
            morto = getattr(alvo, "hp", 0) <= 0
            resultado = evento("ataque", de=self.nome, para=nome(alvo), acertou=True, dano=dano, critico=False)
            resultado["eventos"] = [resultado]
            if morto:
                resultado["eventos"].append(evento("morte", de=nome(alvo)))
            return resultado
        resultado = evento("ataque", de=self.nome, para=nome(alvo), acertou=False, dano=0, critico=False)
        resultado["eventos"] = [resultado]
        return resultado

    def __repr__(self):
        return f"Monstro(nome={self.nome}, hp={self.hp}, dano={self.dano})"
