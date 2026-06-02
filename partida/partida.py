from jogador import Jogador


class Partida:
    def __init__(self, jogadores: list[Jogador]):
        self.jogadores = jogadores
        self.mortos: list[Jogador] = []
        self.rodada = 1

    @classmethod
    def registrar_jogadores(cls, qj: int) -> list[Jogador]:
        jogadores = []
        print("\n=== Criação de personagens (D&D 5e simplificado) ===\n")
        for i in range(qj):
            jogadores.append(Jogador.criar(i))
        return jogadores

    def ordenar_iniciativa(self) -> list[Jogador]:
        ordem = sorted(self.jogadores, key=lambda j: j.rolar_iniciativa(), reverse=True)
        print("\nOrdem de iniciativa:")
        for j in ordem:
            print(f"  {j.nome}")
        return ordem

    def verificar_morte(self):
        for jogador in self.jogadores[:]:
            if jogador.hp <= 0:
                print(f"\n{jogador.nome} caiu em combate!")
                self.mortos.append(jogador)
                self.jogadores.remove(jogador)

    def fim_partida(self) -> bool:
        if len(self.jogadores) <= 1:
            if self.jogadores and self.jogadores[0].hp > 0:
                campeao = self.jogadores[0]
                print(f"\n{'='*40}")
                print(f"  {campeao.nome} venceu a arena!")
                print(f"  Nível {campeao.nivel} | {campeao.ouro} PO")
                print(f"{'='*40}\n")
            else:
                print("\nTodos foram derrotados. Fim da partida.\n")
            return True
        return False

    def status_geral(self):
        print(f"\n--- Rodada {self.rodada} ---")
        for j in self.jogadores:
            print(f"  {j.status()}")
        if self.mortos:
            print("  Derrotados:", ", ".join(m.nome for m in self.mortos))
