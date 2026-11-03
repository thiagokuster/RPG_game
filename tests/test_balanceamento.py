import random
import unittest
from collections import Counter

from jogador import Jogador
from loja import Loja
from partida import Partida
from combate import resolver_ataque


NOMES = ["Ana", "Bruno", "Carla", "Diego", "Eva"]


def _inimigos(jogador, partida):
    return [alvo for alvo in partida.vivos() if alvo is not jogador]


def _magias(jogador, tipo):
    return [magia for magia in jogador.magias if magia.tipo == tipo and jogador.mana >= magia.custo]


def _comprar_e_equipar(jogador, loja):
    for item in list(loja.estoque):
        if jogador.moedas < item.valor:
            continue
        ocupado = (
            (item.tipo == "arma" and jogador.arma)
            or (item.tipo == "armadura" and jogador.armadura)
            or (item.tipo == "anel" and jogador.anel)
        )
        if ocupado:
            continue
        jogador.moedas -= item.valor
        loja.estoque.remove(item)
        jogador.adicionar_item_inventario(item)
        jogador.equipar(item)
        return item.tipo
    return None


def _agir(jogador, partida, loja):
    inimigos = _inimigos(jogador, partida)
    if not inimigos:
        return "nenhum"

    ferido = jogador.hp <= jogador.max_hp * 0.55
    curas = _magias(jogador, "cura")
    if ferido and curas:
        jogador.usar_magia(curas[0].nome, jogador)
        return "cura"

    danos = _magias(jogador, "dano")
    if danos:
        alvo = min(inimigos, key=lambda outro: (outro.hp, -outro.armor_class))
        jogador.usar_magia(danos[0].nome, alvo)
        return "magia"

    compra = _comprar_e_equipar(jogador, loja)
    if compra:
        return f"loja_{compra}"

    alvo = min(inimigos, key=lambda outro: (outro.hp, -outro.armor_class))
    resolver_ataque(jogador, alvo)
    return "ataque"


def _avancar(partida, loja, atual, turno, rodada):
    indice = partida.jogadores.index(atual) if atual in partida.jogadores else 0
    proximo = partida.proximo_vivo(atual)
    turno += 1
    if proximo is not None:
        if partida.jogadores.index(proximo) <= indice:
            rodada += 1
            partida.iniciar_rodada()
            loja.chance_att_loja()
        proximo.iniciar_turno()
    return proximo, turno, rodada


def simular_partida(seed):
    random.seed(seed)
    jogadores = Jogador.criar_elenco(NOMES)
    partida = Partida(jogadores)
    loja = Loja()
    atual = jogadores[0]
    turno = 1
    rodada = 1
    usos = Counter()

    while not partida.fim_partida() and turno <= 250:
        if atual is None or atual.hp <= 0:
            vivos = partida.vivos()
            if not vivos:
                break
            atual = vivos[0]

        loja.turno = max(1, rodada)
        evento = partida.gerar_evento_aleatorio(rodada, atual)
        if evento:
            tipo = evento.get("tipo") or "evento"
            usos["eventos"] += 1
            usos[f"evento_{tipo}"] += 1
            partida.resolver_evento_aleatorio(atual, evento, rodada)
            partida.verificar_mortos()
            atual, turno, rodada = _avancar(partida, loja, atual, turno, rodada)
            continue

        atual.iniciar_turno()
        acao = _agir(atual, partida, loja)
        usos[acao] += 1
        partida.verificar_mortos()
        if acao == "ataque" and atual.hp > 0:
            Partida.ganhar_moeda(atual, rodada)
            atual.ganhar_experiencia(25)
        atual, turno, rodada = _avancar(partida, loja, atual, turno, rodada)

    vivos = partida.vivos()
    return {
        "seed": seed,
        "turnos": turno,
        "rodadas": rodada,
        "vencedor": vivos[0].nome if len(vivos) == 1 else None,
        "usos": usos,
    }


class TestBalanceamento(unittest.TestCase):
    def test_simula_partidas_com_sementes_registradas(self):
        seeds = list(range(40))
        resultados = [simular_partida(seed) for seed in seeds]

        self.assertEqual(len(resultados), 40)
        self.assertTrue(all(item["turnos"] > 0 for item in resultados))

        vitorias = Counter(item["vencedor"] for item in resultados if item["vencedor"])
        usos = Counter()
        for item in resultados:
            usos.update(item["usos"])
        duracao_media = sum(item["turnos"] for item in resultados) / len(resultados)

        self.assertGreater(usos["magia"] + usos["cura"], 0)
        self.assertGreater(usos["eventos"], 0)
        self.assertGreaterEqual(len(vitorias), 2)
        self.assertLess(duracao_media, 250)


if __name__ == "__main__":
    unittest.main(verbosity=2)
