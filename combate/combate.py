from jogador import Jogador
from sistema.dados import rolar


class Combate:
    def __init__(self, jog: Jogador, jogadores: list[Jogador], indice: int):
        self.jog = jog
        self.jogadores = jogadores
        self.indice = indice

    def escolher_alvo(self) -> Jogador | None:
        vivos = [(i, j) for i, j in enumerate(self.jogadores) if i != self.indice and j.hp > 0]
        if not vivos:
            print("Não há alvos disponíveis.")
            return None
        if len(vivos) == 1:
            return vivos[0][1]
        for i, jogador in vivos:
            print(f"  [{i}] {jogador.nome} — HP {jogador.hp}/{jogador.hp_max} | CA {jogador.ca}")
        while True:
            try:
                ialvo = int(input("Alvo: "))
                for i, jogador in vivos:
                    if i == ialvo:
                        return jogador
            except ValueError:
                pass
            print("Alvo inválido.")

    def atacar(self):
        alvo = self.escolher_alvo()
        if not alvo:
            return

        print(f"\n{self.jog.nome} ataca {alvo.nome}!")
        d20 = self.jog.rolar_d20("ataque")
        total_ataque = d20 + self.jog.bonus_ataque()

        if d20 == 1:
            print("Falha crítica! O ataque erra automaticamente.")
            return
        if d20 == 20:
            print("Acerto crítico! (dados de dano dobrados)")
        elif total_ataque < alvo.ca:
            print(f"Errou! ({total_ataque} vs CA {alvo.ca})")
            return
        else:
            print(f"Acertou! ({total_ataque} vs CA {alvo.ca})")

        critico = d20 == 20
        dano = self.jog.calcular_dano(critico=critico)
        alvo.hp -= dano
        print(f"{alvo.nome} perde {dano} HP! Restam {max(0, alvo.hp)}/{alvo.hp_max}.")

        if alvo.hp <= 0:
            print(f"{alvo.nome} foi derrotado!")
            self.jog.ganhar_xp(50)
            self.jog.ouro += rolar("1d6") * 5

    def acao_magia(self):
        alvo = self.escolher_alvo()
        if alvo:
            self.jog.conjurar_magia(alvo if alvo != self.jog else self.jog)
