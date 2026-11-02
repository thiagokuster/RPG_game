from jogador import Jogador


def aplicar_dano(alvo, dano):
    dano = max(0, int(dano))
    if hasattr(alvo, "receber_dano"):
        return alvo.receber_dano(dano)
    alvo.hp = max(0, getattr(alvo, "hp", 0) - dano)
    return {"dano": dano, "reduzido": 0, "quebrou": False, "bruto": dano}


def resolver_ataque(atacante, alvo):
    if alvo is None or alvo is atacante:
        return {"acertou": False, "dano": 0, "critico": False, "motivo": "alvo_invalido"}
    if getattr(atacante, "hp", 0) <= 0:
        return {"acertou": False, "dano": 0, "critico": False, "motivo": "atacante_morto"}
    if getattr(alvo, "hp", 0) <= 0:
        return {"acertou": False, "dano": 0, "critico": False, "motivo": "alvo_morto"}

    dado_ataque = atacante.d20()
    ataque_total = dado_ataque + atacante.bonus_ataque_total
    ca = getattr(alvo, "armor_class", 12)

    if ataque_total < ca:
        print(f"{alvo.nome} resistiu ao ataque! Defesa: {ca}")
        return {
            "acertou": False,
            "dano": 0,
            "critico": False,
            "dado": dado_ataque,
            "total": ataque_total,
            "motivo": "erro",
        }

    d10 = atacante.d10()
    bruto = atacante.danotot(d10, dado_ataque)
    aplicado = aplicar_dano(alvo, bruto)
    print(f"{alvo.nome} perdeu {aplicado['dano']} de HP!")
    if aplicado.get("reduzido"):
        print(f"A armadura absorveu {aplicado['reduzido']} de dano.")
    if aplicado.get("quebrou"):
        print(f"A armadura de {alvo.nome} quebrou e foi removida.")
    return {
        "acertou": True,
        "dano": aplicado["dano"],
        "reduzido": aplicado.get("reduzido", 0),
        "armadura_quebra": aplicado.get("quebrou", False),
        "critico": dado_ataque >= getattr(atacante, "critico", 20),
        "dado": dado_ataque,
        "total": ataque_total,
        "motivo": "acerto",
    }


class Combate:
    def __init__(self, jog, jogadores, indice):
        self.jog: Jogador = jog
        self.jogadores = jogadores
        self.indice = indice
        self.qj = len(self.jogadores)
        self.alvo: Jogador = None

    def alvos_disponiveis(self):
        return [
            (i, jogador)
            for i, jogador in enumerate(self.jogadores)
            if jogador is not self.jog and jogador.hp > 0
        ]

    def escolher_alvo(self):
        alvos = self.alvos_disponiveis()
        if not alvos:
            print("Nenhum alvo disponivel")
            return False

        if len(alvos) == 1:
            self.alvo = alvos[0][1]
            return True

        while True:
            for i, jogador in alvos:
                print(f"- [{i}] {jogador.nome}")
            print("- [-1] Voltar")
            try:
                ialvo = int(input("Escolha quem voce vai atacar: "))
                if ialvo == -1:
                    return False
                if ialvo == self.indice or self.jogadores[ialvo] is self.jog:
                    print("Voce nao pode se atacar!")
                    continue
                escolhido = next((jogador for i, jogador in alvos if i == ialvo), None)
                if escolhido is None:
                    print("Alvo invalido")
                    continue
                self.alvo = escolhido
                return True
            except (ValueError, IndexError):
                print("Digite um valor valido")

    def atacar(self):
        if not self.escolher_alvo():
            return None
        return resolver_ataque(self.jog, self.alvo)["acertou"]
