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
        self.onda = 1
        self.turnos = 0

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
    def gerar_chefe(cls, onda=1, jogadores=2):
        n = max(2, int(jogadores or 2))
        fator_hp = 0.5 + 0.55 * n
        fator_dano = 0.75 + 0.2 * n
        hp = int((40 + onda * 18) * fator_hp)
        chefe = cls(
            nome=f"Chefe da onda {onda}",
            hp=hp,
            ataque_bonus=4 + onda + (n - 2),
            armor_class=13 + min(4, onda),
            dano=max(1, int((8 + onda) * fator_dano)),
            xp=40 + onda * 15,
            recompensa=20 + onda * 8,
            tipo="chefe",
        )
        chefe.onda = onda
        chefe.grupo = n
        return chefe

    @staticmethod
    def escolher_alvo(jogadores):
        vivos = [jogador for jogador in jogadores if getattr(jogador, "hp", 0) > 0]
        if not vivos:
            return None
        if randint(1, 10) <= 7:
            return min(vivos, key=lambda jogador: (jogador.hp, getattr(jogador, "max_hp", jogador.hp)))
        return choice(vivos)

    def pisada(self, alvos):
        vivos = sorted(
            [jogador for jogador in alvos if getattr(jogador, "hp", 0) > 0],
            key=lambda jogador: (jogador.hp, getattr(jogador, "max_hp", jogador.hp)),
        )[:2]
        eventos = []
        bruto = 6 + max(1, self.ataque_bonus // 2)
        for alvo in vivos:
            if hasattr(alvo, "receber_dano"):
                dano = alvo.receber_dano(bruto)["dano"]
            else:
                alvo.hp = max(0, getattr(alvo, "hp", 0) - bruto)
                dano = bruto
            ev = evento("magia", de=self.nome, para=nome(alvo), magia="Pisada", dano=dano, acertou=True, cura=0)
            eventos.append(ev)
            if getattr(alvo, "hp", 0) <= 0:
                eventos.append(evento("morte", de=nome(alvo)))
        resultado = evento("magia", de=self.nome, magia="Pisada", acertou=True, dano=bruto)
        resultado["eventos"] = eventos
        return resultado

    def _golpes_por_turno(self):
        n = max(2, int(getattr(self, "grupo", 2) or 2))
        return max(1, 1 + (n - 2) // 3)

    def _fundir_golpes(self, alvos, inicial=None):
        eventos = list((inicial or {}).get("eventos") or ([inicial] if inicial else []))
        golpes = self._golpes_por_turno()
        if inicial is not None:
            golpes = max(0, golpes - 1)
        ultimo = inicial
        for _ in range(golpes):
            vivos = [jogador for jogador in alvos if getattr(jogador, "hp", 0) > 0]
            alvo = self.escolher_alvo(vivos)
            if alvo is None:
                break
            ultimo = self.atacar(alvo)
            eventos.extend(ultimo.get("eventos") or [ultimo])
        if ultimo is None:
            resultado = evento("ataque", de=self.nome, acertou=False, dano=0)
            resultado["eventos"] = eventos or [resultado]
            return resultado
        ultimo = dict(ultimo)
        ultimo["eventos"] = eventos
        return ultimo

    def agir(self, alvos):
        self.turnos += 1
        vivos = [jogador for jogador in alvos if getattr(jogador, "hp", 0) > 0]
        if self.tipo == "chefe" and self.turnos % 3 == 0 and len(vivos) >= 2:
            return self._fundir_golpes(alvos, self.pisada(vivos))
        return self._fundir_golpes(alvos)

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
