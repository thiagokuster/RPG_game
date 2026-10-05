import io
import random
import statistics
from contextlib import redirect_stdout

from combate.combate import Combate
from jogador.jogador import Jogador
from loja.loja import Loja
from partida.partida import Partida


def simular(seed):
    random.seed(seed)
    classes = ["Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo", "Guerreiro"]
    jogadores = [Jogador.criar_por_classe(f"Jogador {i + 1}", classes[i]) for i in range(6)]
    partida = Partida(jogadores)
    partida.verificar_mortos()
    jogatual = 0
    turno = 1
    rodada = 1
    loja = Loja()

    with redirect_stdout(io.StringIO()):
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

            alvos = [i for i in range(len(jogadores)) if i != jogatual and jogadores[i].hp > 0]
            if not alvos:
                break

            combate = Combate(jog=jog, jogadores=jogadores, indice=jogatual)
            combate.alvo = jogadores[alvos[0]]
            acerto = combate.atacar()
            if acerto:
                Partida.ganhar_moeda(rodada=rodada, jog=jog)
                jog.ganhar_experiencia(25)

            jogatual = (jogatual + 1) % len(jogadores)
            if jogatual == 0:
                loja.chance_att_loja()
                rodada += 1
            turno += 1

    vivos = [j for j in jogadores if j.hp > 0]
    return {"seed": seed, "rodadas": rodada, "turnos": turno, "vivos": len(vivos), "vencedor": vivos[0].nome if len(vivos) == 1 else None}

resultados = [simular(seed) for seed in range(1, 11)]
print('RESULTADOS_6_JOGADORES')
for r in resultados:
    print(r)
rodadas = [r['rodadas'] for r in resultados]
turnos = [r['turnos'] for r in resultados]
print(f"MEDIA_RODADAS={statistics.mean(rodadas):.2f}")
print(f"MEDIANA_RODADAS={statistics.median(rodadas):.2f}")
print(f"MEDIA_TURNOS={statistics.mean(turnos):.2f}")
print(f"MEDIANA_TURNOS={statistics.median(turnos):.2f}")
print(f"VITORIAS_UNICAS={sum(1 for r in resultados if r['vencedor'] is not None)}")
print(f"DERROTAS_TOTAIS={sum(1 for r in resultados if r['vivos'] == 0)}")
