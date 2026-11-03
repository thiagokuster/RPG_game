def evento(tipo, **campos):
    dados = {"tipo": tipo}
    dados.update(campos)
    return dados


def nome(entidade):
    if entidade is None:
        return ""
    return getattr(entidade, "nome", str(entidade))


def texto(ev):
    if not ev:
        return ""
    tipo = ev.get("tipo")
    de = ev.get("de", "")
    para = ev.get("para", "")
    if tipo == "ataque":
        if not ev.get("acertou"):
            return f"{para or de} resistiu ao ataque."
        critico = " Crítico!" if ev.get("critico") else ""
        return f"{de} atacou {para} e causou {ev.get('dano', 0)} de dano.{critico}"
    if tipo == "magia":
        if ev.get("cura"):
            return f"{de} usou {ev.get('magia')} e curou {ev.get('cura')} em {para}."
        return f"{de} lançou {ev.get('magia')} em {para} e causou {ev.get('dano', 0)} de dano."
    if tipo == "dano":
        return f"{para or de} perdeu {ev.get('dano', 0)} de HP."
    if tipo == "cura":
        return f"{para or de} recuperou {ev.get('cura', 0)} de HP."
    if tipo == "morte":
        return f"{de} morreu."
    if tipo == "fim":
        vencedor = ev.get("vencedor")
        if vencedor:
            return f"{vencedor} venceu a partida."
        return "A partida encerrou sem vencedor."
    if tipo == "nivel":
        return f"{de} subiu para o nível {ev.get('nivel')}."
    if tipo == "moedas":
        return f"{de} ganhou {ev.get('moedas', 0)} moedas."
    if tipo == "tesouro":
        return f"{de} encontrou um tesouro e ganhou {ev.get('moedas', 0)} moedas."
    if tipo == "risco":
        if ev.get("resultado") == "evitou":
            return f"{de} evitou um golpe de azar."
        return f"{de} perdeu {ev.get('moedas', 0)} moedas num evento de risco."
    if tipo == "aposta":
        if ev.get("resultado") == "sem_moedas":
            return f"{de} não tinha moedas para apostar."
        if ev.get("resultado") == "ganhou":
            return f"{de} apostou {ev.get('aposta', 0)} e ganhou {ev.get('moedas', 0)} moedas."
        return f"{de} apostou {ev.get('aposta', 0)} e perdeu."
    if tipo == "onda":
        return f"{de} surgiu na onda {ev.get('onda')}."
    if tipo == "monstro":
        return f"Um {ev.get('nome', 'monstro')} apareceu."
    if tipo == "armadura":
        if ev.get("quebrou"):
            return f"A armadura de {de} quebrou."
        return f"A armadura de {de} absorveu {ev.get('reduzido', 0)} de dano."
    if tipo == "item":
        return f"{de} recebeu {ev.get('item')}."
    if tipo == "equipar":
        return f"{de} equipou {ev.get('item')}."
    if tipo == "loja":
        if ev.get("resultado") == "compra":
            return f"{de} comprou {ev.get('item')}."
        return f"{de} atualizou a loja."
    if tipo == "erro":
        return ev.get("motivo") or ev.get("mensagem") or "Ação inválida."
    return ev.get("texto") or tipo


def textos(eventos):
    return [texto(ev) for ev in eventos or [] if ev]
