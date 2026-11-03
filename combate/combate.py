from jogador import Jogador
from motor.eventos import evento, nome


def aplicar_dano(alvo, dano):
    dano = max(0, int(dano))
    if hasattr(alvo, "receber_dano"):
        return alvo.receber_dano(dano)
    alvo.hp = max(0, getattr(alvo, "hp", 0) - dano)
    return {"dano": dano, "reduzido": 0, "quebrou": False, "bruto": dano}


def resolver_ataque(atacante, alvo):
    de = nome(atacante)
    para = nome(alvo)
    if alvo is None or alvo is atacante:
        return {
            "tipo": "ataque",
            "de": de,
            "para": para,
            "acertou": False,
            "dano": 0,
            "critico": False,
            "motivo": "alvo_invalido",
            "eventos": [evento("ataque", de=de, para=para, acertou=False, dano=0, critico=False, motivo="alvo_invalido")],
        }
    if getattr(atacante, "hp", 0) <= 0:
        return {
            "tipo": "ataque",
            "de": de,
            "para": para,
            "acertou": False,
            "dano": 0,
            "critico": False,
            "motivo": "atacante_morto",
            "eventos": [evento("ataque", de=de, para=para, acertou=False, dano=0, critico=False, motivo="atacante_morto")],
        }
    if getattr(alvo, "hp", 0) <= 0:
        return {
            "tipo": "ataque",
            "de": de,
            "para": para,
            "acertou": False,
            "dano": 0,
            "critico": False,
            "motivo": "alvo_morto",
            "eventos": [evento("ataque", de=de, para=para, acertou=False, dano=0, critico=False, motivo="alvo_morto")],
        }

    dado_ataque = atacante.d20()
    ataque_total = dado_ataque + atacante.bonus_ataque_total
    ca = getattr(alvo, "armor_class", 12)
    critico = dado_ataque >= getattr(atacante, "critico", 20)

    if ataque_total < ca:
        ev = evento("ataque", de=de, para=para, acertou=False, dano=0, critico=False, dado=dado_ataque, total=ataque_total, motivo="erro")
        return {
            "tipo": "ataque",
            "de": de,
            "para": para,
            "acertou": False,
            "dano": 0,
            "critico": False,
            "dado": dado_ataque,
            "total": ataque_total,
            "motivo": "erro",
            "eventos": [ev],
        }

    d10 = atacante.d10()
    bruto = atacante.danotot(d10, dado_ataque)
    aplicado = aplicar_dano(alvo, bruto)
    eventos = [
        evento(
            "ataque",
            de=de,
            para=para,
            acertou=True,
            dano=aplicado["dano"],
            critico=critico,
            dado=dado_ataque,
            total=ataque_total,
            motivo="acerto",
        )
    ]
    if aplicado.get("reduzido"):
        eventos.append(evento("armadura", de=para, reduzido=aplicado["reduzido"], quebrou=False))
    if aplicado.get("quebrou"):
        eventos.append(evento("armadura", de=para, reduzido=aplicado.get("reduzido", 0), quebrou=True))
    if getattr(alvo, "hp", 0) <= 0:
        eventos.append(evento("morte", de=para))
    return {
        "tipo": "ataque",
        "de": de,
        "para": para,
        "acertou": True,
        "dano": aplicado["dano"],
        "reduzido": aplicado.get("reduzido", 0),
        "armadura_quebra": aplicado.get("quebrou", False),
        "critico": critico,
        "dado": dado_ataque,
        "total": ataque_total,
        "motivo": "acerto",
        "eventos": eventos,
    }


class Combate:
    def __init__(self, jog, jogadores, indice):
        self.jog: Jogador = jog
        self.jogadores = jogadores
        self.indice = indice
        self.qj = len(self.jogadores)
        self.alvo: Jogador = None
        self.ultimo = None

    def alvos_disponiveis(self):
        return [
            (i, jogador)
            for i, jogador in enumerate(self.jogadores)
            if jogador is not self.jog and jogador.hp > 0
        ]

    def atacar(self, alvo=None):
        if alvo is not None:
            self.alvo = alvo
        if self.alvo is None:
            alvos = self.alvos_disponiveis()
            if len(alvos) == 1:
                self.alvo = alvos[0][1]
            else:
                return None
        self.ultimo = resolver_ataque(self.jog, self.alvo)
        return self.ultimo["acertou"]
