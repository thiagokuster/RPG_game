from random import choice, randint


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
        nome, hp, ataque_bonus, armor_class, dano, xp, recompensa, tipo = escolha

        if nivel >= 4:
            nome = choice([nome, "Bandido da Selva", "Basilisco Pequeno", "Rastejador"])
            hp += 15
            ataque_bonus += 1
            dano += 2
            recompensa += 10

        return cls(nome, hp, ataque_bonus, armor_class, dano, xp, recompensa, tipo)

    def atacar(self, alvo):
        ataque = randint(1, 20) + self.ataque_bonus
        if ataque >= getattr(alvo, "armor_class", 12):
            dano = randint(1, self.dano) + max(1, self.ataque_bonus // 2)
            alvo.hp = max(0, alvo.hp - dano)
            print(f"{self.nome} atingiu {alvo.nome} e causou {dano} de dano!")
            return dano
        print(f"{self.nome} errou o ataque contra {alvo.nome}.")
        return 0

    def __repr__(self):
        return f"Monstro(nome={self.nome}, hp={self.hp}, dano={self.dano})"
