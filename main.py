from combate import Combate
from jogador import Jogador
from loja import Loja
from partida import Partida
from equipamento import Equipamento
from sistema.classes_rpg import CLASSES


def equipamento_inicial(jogadores: list[Jogador]):
    """Itens de partida para agilizar o primeiro combate."""
    if not jogadores:
        return
    espada = Equipamento("Espada enferrujada", dado_dano="1d6", valor=5, tipo="arma")
    escudo = Equipamento("Escudo de madeira", bonus_ca=2, valor=10, tipo="armadura")
    jogadores[0].add_item_inventario(espada)
    jogadores[0].equipar(espada)
    if len(jogadores) > 1:
        jogadores[1].add_item_inventario(escudo)
        jogadores[1].equipar(escudo)


def menu_turno(jogador: Jogador) -> int:
    magia = "  [4] Conjurar magia\n" if CLASSES[jogador.classe].get("magia") else ""
    print(f"""
╔══ Turno de {jogador.nome} ══╗
  {jogador.status()}
  [1] Atacar (d20 + mod vs CA)
  [2] Loja do mercador
  [3] Inventário / equipar
{magia}  [5] Descanso curto (1d8+CON)
  [6] Ver ficha completa
  [7] Passar turno
╚══════════════════════════╝""")
    try:
        return int(input("Ação: "))
    except ValueError:
        return 0


def main():
    print("=" * 50)
    print("  ARENA RPG — inspirado em D&D 5ª Edição")
    print("=" * 50)

    try:
        qj = int(input("\nQuantos jogadores? (2-6): "))
        qj = max(2, min(6, qj))
    except ValueError:
        qj = 2
        print("Usando 2 jogadores.")

    jogadores = Partida.registrar_jogadores(qj)
    partida = Partida(jogadores)
    equipamento_inicial(jogadores)

    print("\nRolando iniciativa da rodada 1...")
    ordem = partida.ordenar_iniciativa()
    turno_idx = 0
    descanso_longo_a_cada = 3

    while True:
        partida.verificar_morte()
        if partida.fim_partida():
            break

        if turno_idx >= len(ordem):
            turno_idx = 0
            partida.rodada += 1
            if partida.rodada % descanso_longo_a_cada == 0:
                print("\n*** Descanso longo entre rodadas — todos recuperam HP ***")
                for j in partida.jogadores:
                    j.descanso_longo()
            print(f"\n>>> Rodada {partida.rodada} <<<")
            ordem = [j for j in ordem if j in partida.jogadores]
            if not ordem:
                break

        jogador = ordem[turno_idx]
        if jogador not in partida.jogadores:
            turno_idx += 1
            continue

        partida.status_geral()
        opc = menu_turno(jogador)

        if opc == 1:
            indice = partida.jogadores.index(jogador)
            Combate(jogador, partida.jogadores, indice).atacar()
            turno_idx += 1
        elif opc == 2:
            Loja.abrir(jogador)
        elif opc == 3:
            jogador.mostrar_inventario()
        elif opc == 4 and CLASSES[jogador.classe].get("magia"):
            indice = partida.jogadores.index(jogador)
            Combate(jogador, partida.jogadores, indice).acao_magia()
            turno_idx += 1
        elif opc == 5:
            jogador.descanso_curto()
            turno_idx += 1
        elif opc == 6:
            jogador.mostrar_ficha()
        elif opc == 7:
            turno_idx += 1
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
