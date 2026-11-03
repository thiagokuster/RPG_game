from combate import resolver_ataque
from equipamento import Equipamento
from motor.eventos import evento, textos
from partida import Partida


def jogador_por_nome(partida, nome):
    return next((item for item in partida.jogadores if item.nome == nome), None)


def resolver_jogada(
    partida,
    jogador,
    acao,
    *,
    alvo_nome=None,
    magia=None,
    item_index=None,
    action_type=None,
    shop=None,
    rodada=1,
):
    shop = list(shop or [])
    if acao == "attack":
        alvo = jogador_por_nome(partida, alvo_nome) if alvo_nome else next(
            (item for item in partida.jogadores if item is not jogador and item.hp > 0),
            None,
        )
        if alvo is None or alvo.hp <= 0 or alvo is jogador:
            return {"ok": False, "erro": "Alvo inválido.", "eventos": []}
        resultado = resolver_ataque(jogador, alvo)
        eventos = list(resultado.get("eventos") or [resultado])
        if resultado["acertou"]:
            extra = Partida.ganhar_moeda(jogador, rodada)
            if extra:
                eventos.append(extra)
            eventos.extend(jogador.ganhar_experiencia(25) or [])
        return {
            "ok": True,
            "eventos": eventos,
            "result": "hit" if resultado["acertou"] else "miss",
            "damage": resultado["dano"],
            "critico": resultado.get("critico", False),
            "target": alvo.nome,
            "shop": shop,
            "extra": False,
        }

    if acao == "shop":
        if action_type == "refresh":
            if jogador.moedas < 5:
                return {"ok": False, "erro": "Moedas insuficientes.", "eventos": []}
            jogador.moedas -= 5
            nivel = partida.jogadores[0].nivel if partida.jogadores else 1
            shop = Equipamento.gerar_estoque(nivel, 3)
            ev = evento("loja", de=jogador.nome, resultado="atualizar")
            return {"ok": True, "eventos": [ev], "shop": shop, "type": "shop"}
        if item_index is None or not isinstance(item_index, int) or not 0 <= item_index < len(shop):
            return {"ok": False, "erro": "Item inválido.", "eventos": []}
        item = shop[item_index]
        if jogador.moedas < item.valor:
            return {"ok": False, "erro": "Moedas insuficientes.", "eventos": []}
        jogador.moedas -= item.valor
        jogador.adicionar_item_inventario(item)
        del shop[item_index]
        ev = evento("loja", de=jogador.nome, resultado="compra", item=item.nome)
        return {
            "ok": True,
            "eventos": [ev],
            "shop": shop,
            "type": "shop",
            "result": "purchase",
            "item": item.nome,
        }

    if acao == "equip":
        if item_index is None or not isinstance(item_index, int) or not 0 <= item_index < len(jogador.inventario):
            return {"ok": False, "erro": "Item inválido.", "eventos": []}
        item = jogador.inventario[item_index]
        jogador.equipar(item)
        ev = evento("equipar", de=jogador.nome, item=item.nome)
        return {"ok": True, "eventos": [ev], "shop": shop, "type": "inventory", "item": item.nome}

    if acao == "use_magic":
        alvo = jogador_por_nome(partida, alvo_nome)
        magia_obj = next((item for item in jogador.magias if item.nome.lower() == str(magia or "").lower()), None)
        if alvo is None or magia_obj is None:
            return {"ok": False, "erro": "Magia inválida.", "eventos": []}
        if magia_obj.tipo == "cura" and alvo.hp <= 0:
            return {"ok": False, "erro": "Não é possível curar um jogador eliminado.", "eventos": []}
        if magia_obj.tipo == "dano" and alvo.hp <= 0:
            return {"ok": False, "erro": "O alvo já está morto.", "eventos": []}
        resultado = jogador.usar_magia(magia_obj.nome, alvo)
        if not resultado:
            return {"ok": False, "erro": "Magia indisponível.", "eventos": []}
        eventos = resultado.get("eventos") if isinstance(resultado, dict) else [resultado]
        return {
            "ok": True,
            "eventos": eventos,
            "shop": shop,
            "type": "magic",
            "magic": magia_obj.nome,
            "target": alvo.nome,
            "extra": False,
        }

    return {"ok": False, "erro": "Ação indisponível.", "eventos": []}


def serializar_eventos(eventos):
    limpos = []
    for ev in eventos or []:
        if not isinstance(ev, dict):
            continue
        limpo = {chave: valor for chave, valor in ev.items() if chave != "monstro" and not hasattr(valor, "hp")}
        limpo.setdefault("texto", textos([ev])[0] if textos([ev]) else "")
        limpos.append(limpo)
    return limpos
