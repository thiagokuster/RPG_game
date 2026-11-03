from combate import Combate
from motor.eventos import texto
from partida import Partida


def cabecalho(titulo: str):
    print("\n" + "=" * 80)
    print(f"{titulo:^80}")
    print("=" * 80)


def validar_opc(lista=None, mensagem=">", mnsgvazio="lista vazia"):
    if not lista:
        print(mnsgvazio)
        return None
    while True:
        try:
            opc = int(input(mensagem))
            if opc in lista:
                return opc
            print("Opcao invalida")
        except ValueError:
            print("Digite um valor valido")


def registrar_jogadores(qj):
    return Partida.registrar_jogadores(qj)


def mostrar_eventos(eventos):
    for ev in eventos or []:
        linha = texto(ev)
        if linha:
            print(linha)


def menu(jogadores, jog, turno):
    cabecalho("BATALHA DO RPG")
    print(f"{'JOGADOR':<15} | {'HP':>5} | {'MOEDAS':>7} | {'CA':>4} | {'NIVEL':>5} | {'MANA':>5}")
    print("-" * 90)
    for j in jogadores:
        status = "VIVO" if j.hp > 0 else "MORTO"
        print(f"{j.nome:<15} | {j.hp:>5} | {j.moedas:>7} | {j.armor_class:>4} | {j.nivel:>5} | {j.mana:>5}  [{status}]")
    print("-" * 90)
    print(
        f"TURNO: {turno:02} | VEZ DE: {jog.nome} | "
        f"HP: {jog.hp} | MOEDAS: {jog.moedas} | CA: {jog.armor_class} | "
        f"NIVEL: {jog.nivel} | MANA: {jog.mana}/{jog.max_mana}"
    )
    print("-" * 90)
    print("[1] ATACAR      [2] LOJA      [3] INVENTARIO      [4] MAGIA")
    print("-" * 90)
    arma = jog.arma.nome if jog.arma else "Nenhuma"
    armadura = jog.armadura.nome if jog.armadura else "Nenhuma"
    print(f"ARMA EQUIPADA: {arma}")
    if jog.armadura:
        print(
            f"ARMADURA: {armadura} | redução {getattr(jog.armadura, 'reducao', 0)} | "
            f"durabilidade {getattr(jog.armadura, 'durabilidade', 0)}"
        )
    else:
        print(f"ARMADURA: {armadura}")
    print(f"SORTE: {getattr(jog, 'sorte', 1)}")
    print(f"BONUS DE ATAQUE: +{jog.bonus_ataque_total}")
    if jog.magias:
        print("MAGIAS: " + ", ".join(f"{m.nome} ({m.custo} mana)" for m in jog.magias))
    print("=" * 90)


def escolher_alvo(combate: Combate):
    alvos = combate.alvos_disponiveis()
    if not alvos:
        print("Nenhum alvo disponivel")
        return False
    if len(alvos) == 1:
        combate.alvo = alvos[0][1]
        return True
    while True:
        for i, jogador in alvos:
            print(f"- [{i}] {jogador.nome}")
        print("- [-1] Voltar")
        ialvo = validar_opc([i for i, _ in alvos] + [-1], "Escolha quem voce vai atacar: ")
        if ialvo is None or ialvo == -1:
            return False
        escolhido = next((jogador for i, jogador in alvos if i == ialvo), None)
        if escolhido is None or escolhido is combate.jog:
            print("Alvo invalido")
            continue
        combate.alvo = escolhido
        return True


def escolher_e_usar_magia(partida, jog):
    if not jog.magias:
        print("Voce nao conhece magias.")
        return None
    print("Magias:")
    for i, magia in enumerate(jog.magias):
        print(f"- [{i}] {magia.nome} ({magia.tipo}, custo {magia.custo})")
    print("- [-1] Voltar")
    opc = validar_opc(list(range(len(jog.magias))) + [-1], "Magia: ")
    if opc is None or opc == -1:
        return None
    magia = jog.magias[opc]
    if magia.tipo == "cura":
        alvos = [alvo for alvo in partida.jogadores if alvo.hp > 0]
    else:
        alvos = [alvo for alvo in partida.jogadores if alvo is not jog and alvo.hp > 0]
    if not alvos:
        print("Nenhum alvo disponivel.")
        return False
    if len(alvos) == 1:
        alvo = alvos[0]
    else:
        for i, alvo in enumerate(alvos):
            print(f"- [{i}] {alvo.nome} HP {alvo.hp}")
        indice = validar_opc(list(range(len(alvos))), "Alvo: ")
        if indice is None:
            return None
        alvo = alvos[indice]
    resultado = jog.usar_magia(magia.nome, alvo)
    mostrar_eventos(resultado.get("eventos") if isinstance(resultado, dict) else None)
    return resultado


def loop_inventario(jog):
    if not jog.inventario:
        print("Inventario vazio")
        return
    fim = len(jog.inventario)
    print("=== INVENTARIO ===")
    for i, item in enumerate(jog.inventario):
        detalhes = jog.detalhes_item(item)
        print(f"-[{i}] {item.nome} | {item.tipo} | {' | '.join(detalhes) if detalhes else 'sem bonus'}")
    print(f"-[{fim}] Saida")
    opc = validar_opc(list(range(fim + 1)), "Escolha um item do inventario: ")
    if opc is None or opc == fim:
        return
    item = jog.inventario[opc]
    if item.tipo in ["arma", "anel", "armadura"]:
        jog.equipar(item)
        print(f"{jog.nome} equipou {item.nome}")
    else:
        print(f"{item.nome} nao pode ser equipado")


def loop_loja(loja, jog):
    while True:
        print("\n=== LOJA ===")
        if loja.estoque:
            titulos = {"arma": "ARMAS", "armadura": "ARMADURAS", "anel": "ACESSORIOS"}
            grupos = loja._por_categoria()
            for tipo in ("arma", "armadura", "anel"):
                itens = grupos.get(tipo) or []
                if not itens:
                    continue
                print(f"-- {titulos[tipo]} --")
                for item in itens:
                    indice = loja.estoque.index(item)
                    print(f"[{indice}] {item.descricao()}")
        else:
            print("Nenhum equipamento disponivel na loja!")
        print("-=" * 30)
        print(f"[-3] Comprar +1 slot ({loja.preco_slot} moedas)")
        print("[-2] Atualizar a loja (5 moedas)")
        print("[-1] Sair")
        print(f"Suas moedas: {jog.moedas}")
        indice = validar_opc(list(range(len(loja.estoque))) + [-3, -2, -1], "Sua opcao : ")
        if indice is None or indice == -1:
            return
        resultado = loja.comprar(jog, indice)
        if resultado.get("tipo") == "erro":
            print(resultado.get("motivo"))
            continue
        mostrar_eventos([resultado])
