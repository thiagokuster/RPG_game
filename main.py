from combate import Combate
from jogador import Jogador
from loja import Loja
from motor.eventos import texto
from partida import Partida
from ui.terminal import (
    cabecalho,
    escolher_alvo,
    escolher_e_usar_magia,
    loop_inventario,
    menu,
    registrar_jogadores,
    validar_opc,
)


def avancar_turno(partida, loja, jogador_atual, estado, atualizar_loja=False):
    indice_antes = partida.jogadores.index(jogador_atual) if jogador_atual in partida.jogadores else 0
    proximo = partida.proximo_vivo(jogador_atual)
    estado["turno"] += 1
    if proximo is not None:
        indice_depois = partida.jogadores.index(proximo)
        if indice_depois <= indice_antes:
            estado["rodada"] += 1
            partida.iniciar_rodada()
            if atualizar_loja:
                loja.chance_att_loja()
        proximo.iniciar_turno()
    return proximo


def mostrar(ev):
    if not ev:
        return
    lista = ev if isinstance(ev, list) else [ev]
    for item in lista:
        linha = texto(item) if isinstance(item, dict) else str(item)
        if linha:
            print(linha)


def jogar():
    cabecalho("BEM-VINDO AO RPG DE BATALHA")

    while True:
        try:
            qj = int(input("Quantos jogadores teremos na partida? "))
            if qj <= 1:
                print("So e possivel iniciar uma partida com 2 ou mais jogadores.")
            else:
                break
        except ValueError:
            print("Digite um valor valido (numero).")

    jogadores: list[Jogador] = registrar_jogadores(qj)
    partida = Partida(jogadores)
    partida.verificar_mortos()

    jog = jogadores[0]
    loja = Loja()
    estado = {"turno": 1, "rodada": 1}

    while True:
        partida.verificar_mortos()
        if partida.fim_partida():
            mostrar(partida.resultado_fim())
            break
        if jog is None or jog.hp <= 0:
            vivos = partida.vivos()
            if not vivos:
                partida.fim_partida()
                mostrar(partida.resultado_fim())
                break
            jog = vivos[0]

        loja.turno = estado["turno"]

        evento_rodada = partida.gerar_evento_aleatorio(estado["rodada"], jog)
        if evento_rodada:
            resultado = partida.resolver_evento_aleatorio(jog, evento_rodada, estado["rodada"])
            mostrar(partida.eventos[-6:])
            partida.verificar_mortos()
            if partida.fim_partida():
                mostrar(partida.resultado_fim())
                break
            jog = avancar_turno(partida, loja, jog, estado, atualizar_loja=True)
            continue

        menu(jogadores=jogadores, jog=jog, turno=estado["turno"])
        opc = validar_opc([1, 2, 3, 4], "Suas opcoes : ")

        if opc == 1:
            combate = Combate(jog=jog, jogadores=jogadores, indice=jogadores.index(jog))
            if not escolher_alvo(combate):
                continue
            acerto = combate.atacar()
            mostrar(combate.ultimo.get("eventos") if combate.ultimo else None)
            if acerto is None:
                continue
            if acerto:
                mostrar(Partida.ganhar_moeda(rodada=estado["rodada"], jog=jog))
                jog.ganhar_experiencia(25)
            jog = avancar_turno(partida, loja, jog, estado, atualizar_loja=True)

        elif opc == 2:
            loja.entrar_loja(jog)
            jog = avancar_turno(partida, loja, jog, estado)

        elif opc == 3:
            loop_inventario(jog)
            jog = avancar_turno(partida, loja, jog, estado)

        elif opc == 4:
            resultado = escolher_e_usar_magia(partida, jog)
            if resultado is None:
                continue
            if not getattr(jog, "gasta_turno", True):
                jog.gasta_turno = True
                print(f"{jog.nome} ainda pode agir neste turno.")
                continue
            jog = avancar_turno(partida, loja, jog, estado, atualizar_loja=True)

        else:
            print("Opcao invalida")


def main():
    jogar()


if __name__ == "__main__":
    main()
