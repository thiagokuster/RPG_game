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

        dado_ataque = self.jog.d20()
        bonus_ataque = self.jog.ataque_bonus + self.jog.proficiencia
        ataque_total = dado_ataque + bonus_ataque

        if ataque_total < self.alvo.armor_class:
            print(f"{self.alvo.nome} resistiu ao ataque! Defesa: {self.alvo.armor_class}")
            return False

        d10 = self.jog.d10()
        dano = self.jog.danotot(d10, dado_ataque)

        if dado_ataque == 20:
            dano *= 2
            print("CRITICO! Dano dobrado.")

        if self.jog.arma and self.jog.arma.bonus_ataque:
            dano += self.jog.arma.bonus_ataque

        self.alvo.hp -= dano
        print(f"{self.alvo.nome} perdeu {dano} de HP!")
        return True