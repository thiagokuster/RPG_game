from jogador import Jogador


class Combate:
    def __init__(self, jog, jogadores, indice):
        self.jog: Jogador = jog
        self.jogadores = jogadores
        self.indice = indice
        self.qj = len(self.jogadores)
        self.alvo: Jogador = None

    def escolher_alvo(self):
        if self.qj > 2:
            while True:
                for i in range(self.qj):
                    if i != self.indice:
                        print(f"- [{i}] {self.jogadores[i].nome}")
                print("- [-1] Voltar")
                try:
                    ialvo = int(input("Escolha quem voce vai atacar: "))
                    if ialvo == -1:
                        return False
                    if ialvo == self.indice:
                        print("Voce nao pode se atacar!")
                        continue
                    if ialvo >= self.qj or ialvo < 0:
                        print("Alvo invalido")
                        continue
                    self.alvo = self.jogadores[ialvo]
                    return True
                except ValueError:
                    print("Digite um valor valido")
        else:
            for i in range(self.qj):
                if i != self.indice:
                    ialvo = i
            self.alvo = self.jogadores[ialvo]
            return True

    def atacar(self):
        if not self.escolher_alvo():
            return False
        d20 = self.jog.d20()
        if d20 > 10:
            d10 = self.jog.d10()
            danotot = self.jog.danotot(d10, d20)
            self.alvo.hp -= danotot
            print(f"{self.alvo.nome} perdeu {danotot} de HP!")
        else:
            print("Errou o ataque")

        return True