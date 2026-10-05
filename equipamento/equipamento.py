from random import choice, choices, randint


class Equipamento:
    def __init__(self, nome, dano=0, valor=0, agilidade=0, tipo=None, raridade=None, bonus_ataque=0, armadura=0):
        self.nome = nome
        self.dano = dano
        self.valor = valor
        self.agilidade = agilidade
        self.tipo = tipo
        self.raridade = raridade
        self.bonus_ataque = bonus_ataque
        self.armadura = armadura

    @classmethod
    def gerarEquipamento(cls, turno):
        qualidade = {
            "comum": 0.5,
            "raro": 0.6,
            "epico": 1.1,
            "lendario": 1.7,
            "mitico": 2,
        }
        pesos = [70, 20, 9, 2, 0.5]
        nomes_arma = ["Faca", "Foice", "Espada", "Clava", "Machado", "Adaga", "Katana", "Lança"]
        nomes_armadura = ["Peitoral", "Cota", "Armadura leve", "Armadura pesada", "Escudo"]

        raridade = choices(list(qualidade.keys()), weights=pesos, k=1)[0]
        tipo = choice(["arma", "armadura", "acessorio"])

        if tipo == "arma":
            nome = choice(nomes_arma)
            danomin = 1
            danomax = int(qualidade[raridade] * turno)
            match raridade:
                case "epico":
                    danomin = int(danomax * 0.25)
                case "lendario":
                    danomin = int(danomax * 0.50)
                case "mitico":
                    danomin = int(danomax * 0.80)
            if danomin <= 0 or danomax <= 0:
                danomin = 1
                danomax = 1
            dano = randint(danomin, danomax)
            bonus_ataque = max(0, int(qualidade[raridade] * 2))
            return cls(
                nome=nome,
                dano=dano,
                valor=max(1, int(dano * 0.7)),
                agilidade=0,
                tipo="arma",
                raridade=raridade,
                bonus_ataque=bonus_ataque,
                armadura=0,
            )

        if tipo == "armadura":
            nome = choice(nomes_armadura)
            armadura = 1 + int(qualidade[raridade] * 2)
            return cls(
                nome=nome,
                dano=0,
                valor=max(1, int(armadura * 3)),
                agilidade=0,
                tipo="armadura",
                raridade=raridade,
                bonus_ataque=0,
                armadura=armadura,
            )

        nome = "Amuleto do Valor"
        return cls(
            nome=nome,
            dano=0,
            valor=max(1, int(turno * 2)),
            agilidade=1,
            tipo="anel",
            raridade=raridade,
            bonus_ataque=0,
            armadura=0,
        )