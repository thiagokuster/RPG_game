from random import choice, choices, randint

class Equipamento:
    def __init__(self, nome, dano=0, valor=0, agilidade=0, tipo=None, raridade=None):
        self.nome = nome
        self.dano = dano
        self.valor = valor
        self.agilidade = agilidade
        self.tipo = tipo
        self.raridade = raridade

    @classmethod
    def gerarEquipamento(cls, turno):
        qualidade = {
            "comum": 0.5,
            "raro": 0.6,
            "epico": 1.1,
            "lendario": 1.7,
            "mitico": 2,
        }
        pesos = [ 70, 20, 9, 2, 0.5]
        nomes = ["Faca", "Foice", "Espada", "Clava", "Machado", "Adaga", "Katana", "Luvas"]

        nome = choice(nomes)
        raridade = choices(list(qualidade.keys()), weights=pesos, k=1)[0]
        
        danomin = 1
        danomax = int(qualidade[raridade] * turno)
        match raridade :
            case "epico":
                danomin = int(danomax*0.25)
            case "lendario":
                danomin = int(danomax*0.50)
            case "mitico":
                danomin = int(danomax*0.80)
        if danomin <= 0 or danomax <= 0:
            danomin=1
            danomax=1
        dano = randint(danomin, danomax)
        valor = int(dano * 0.7)
        if valor <= 0:
            valor = 1

        return cls(
            nome=nome,
            dano=dano,
            valor=valor,
            agilidade=0,
            tipo="arma",
            raridade=raridade,
        )