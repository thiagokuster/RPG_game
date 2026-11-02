from random import choice, randint, uniform

from monstro import Monstro


def chance_evento(rodada):
    if rodada <= 2:
        chance = 2
    elif rodada <= 5:
        chance = 4
    elif rodada <= 10:
        chance = 6
    else:
        chance = 8
    return chance + max(0, (rodada - 1) // 10)


def escolher_tipo(sorte=0):
    sorte = max(0, int(sorte or 0))
    pesos = {
        "monstro": 40,
        "tesouro": 20 + sorte * 4,
        "aposta": 20 + sorte * 2,
        "risco": max(8, 20 - sorte * 3),
    }
    urna = []
    for tipo, peso in pesos.items():
        urna.extend([tipo] * max(1, int(peso)))
    return choice(urna)


def resolver_tesouro(jogador, rodada):
    ganho = 2 + max(1, rodada // 2) + getattr(jogador, "sorte", 0)
    jogador.moedas += ganho
    print(f"{jogador.nome} encontrou um tesouro e ganhou {ganho} moedas!")
    return {"tipo": "tesouro", "moedas": ganho, "resultado": "ganhou"}


def resolver_risco(jogador, rodada):
    perda = min(jogador.moedas, 1 + rodada // 3)
    salvamento = randint(1, 20) + getattr(jogador, "sorte", 0)
    if perda <= 0 or salvamento >= 12:
        print(f"{jogador.nome} evitou um golpe de azar.")
        return {"tipo": "risco", "moedas": 0, "resultado": "evitou", "dado": salvamento}
    jogador.moedas -= perda
    print(f"{jogador.nome} perdeu {perda} moedas num evento de risco.")
    return {"tipo": "risco", "moedas": perda, "resultado": "perdeu", "dado": salvamento}


def resolver_aposta(jogador, rodada, aposta=None):
    if jogador.moedas <= 0:
        print(f"{jogador.nome} nao tinha moedas para apostar.")
        return {"tipo": "aposta", "moedas": 0, "resultado": "sem_moedas"}

    aposta = aposta if aposta is not None else min(jogador.moedas, 2 + rodada // 4)
    aposta = max(1, min(jogador.moedas, int(aposta)))
    jogador.moedas -= aposta
    multiplicador = round(uniform(1.0, 2.0), 1)
    dado = randint(1, 20) + getattr(jogador, "sorte", 0)
    if dado >= 11:
        ganho = max(1, int(aposta * multiplicador))
        jogador.moedas += ganho
        print(f"{jogador.nome} apostou {aposta} e ganhou {ganho} moedas ({multiplicador:.1f}x).")
        return {
            "tipo": "aposta",
            "resultado": "ganhou",
            "aposta": aposta,
            "moedas": ganho,
            "multiplicador": multiplicador,
            "dado": dado,
        }
    print(f"{jogador.nome} apostou {aposta} e perdeu.")
    return {"tipo": "aposta", "resultado": "perdeu", "aposta": aposta, "moedas": 0, "dado": dado}


def gerar_evento(rodada, jogador=None):
    sorte = getattr(jogador, "sorte", 0) if jogador else 0
    if randint(1, 100) > chance_evento(rodada) + sorte:
        return None

    tipo = escolher_tipo(sorte)
    if tipo == "monstro":
        nivel = max(1, (rodada // 2) + 1)
        monstro = Monstro.gerar_monstro(nivel)
        print(f"Evento aleatorio! Um {monstro.nome} apareceu na rodada {rodada}.")
        return {"tipo": "monstro", "monstro": monstro}
    if tipo == "tesouro":
        return {"tipo": "tesouro"}
    if tipo == "aposta":
        return {"tipo": "aposta"}
    return {"tipo": "risco"}


def resolver_evento(jogador, evento, rodada=1):
    if not evento:
        return None
    tipo = evento.get("tipo")
    if tipo == "tesouro":
        return resolver_tesouro(jogador, rodada)
    if tipo == "aposta":
        return resolver_aposta(jogador, rodada, evento.get("aposta"))
    if tipo == "risco":
        return resolver_risco(jogador, rodada)
    return evento
