from jogador import Jogador
from combate import Combate
from partida import Partida
from loja import Loja

print("=" * 80)
print("BEM-VINDO AO RPG DE BATALHA".center(80))
print("=" * 80)

while True:
    try:
        qj = int(input("Quantos jogadores teremos na partida? "))
        if qj <= 1:
            print("So e possivel iniciar uma partida com 2 ou mais jogadores.")
        else:
            break
    except ValueError:
        print("Digite um valor valido (numero).")

jogadores: list[Jogador] = Partida.registrar_jogadores(qj=qj, hp=100)
partida = Partida(jogadores)
partida.verificar_mortos()

jogatual = 0
turno = 1
rodada = 1
loja = Loja()

while True:
    partida.verificar_mortos()
    if partida.fim_partida():
        break
    if jogatual >= len(jogadores):
        jogatual = 0

    jog = jogadores[jogatual]
    loja.turno = turno

    evento = partida.gerar_evento_monstro(rodada)
    if evento:
        partida.resolver_evento_monstro(jog, evento)
        if jog.hp <= 0:
            partida.verificar_mortos()
            if partida.fim_partida():
                break
        jogatual = (jogatual + 1) % len(jogadores)
        if jogatual == 0:
            loja.chance_att_loja()
            rodada += 1
        turno += 1
        continue

    Partida.menu(jogadores=jogadores, jog=jog, turno=turno)
    opc = Partida.validar_opc([1, 2, 3], "Suas opcoes : ")

    if opc == 1:
        combate = Combate(jog=jogadores[jogatual], jogadores=jogadores, indice=jogatual)
        acerto = combate.atacar()
        if acerto:
            Partida.ganhar_moeda(rodada=rodada, jog=jog)
            jog.ganhar_experiencia(25)

        jogatual = (jogatual + 1) % len(jogadores)
        if jogatual == 0:
            loja.chance_att_loja()
            rodada += 1
        turno += 1

    elif opc == 2:
        loja.entrar_loja(jog)
        jogatual = (jogatual + 1) % len(jogadores)
        if jogatual == 0:
            rodada += 1
        turno += 1

    elif opc == 3:
        jogadores[jogatual].mostrar_inventario()
        jogatual = (jogatual + 1) % len(jogadores)
        if jogatual == 0:
            rodada += 1
        turno += 1

    else:
        print("Opcao invalida")