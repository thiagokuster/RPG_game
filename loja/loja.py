from equipamento import Equipamento

ITENS_LOJA = [
    Equipamento("Adaga", dado_dano="1d4", valor=2, tipo="arma"),
    Equipamento("Espada longa", dado_dano="1d8", valor=15, tipo="arma"),
    Equipamento("Machado grande", dado_dano="1d12", valor=30, tipo="arma"),
    Equipamento("Arco curto", dado_dano="1d6", valor=25, agilidade=2, tipo="arma"),
    Equipamento("Armadura de couro", bonus_ca=2, agilidade=2, valor=10, tipo="armadura"),
    Equipamento("Cota de malha", bonus_ca=5, agilidade=2, valor=75, tipo="armadura"),
    Equipamento("Placas", bonus_ca=8, agilidade=0, valor=1500, tipo="armadura"),
    Equipamento("Anel de proteção", bonus_ca=1, valor=50, tipo="anel"),
    Equipamento("Anel de precisão", agilidade=1, valor=40, tipo="anel"),
    Equipamento("Poção de cura", dano=0, valor=50, tipo="consumivel"),
]


class Loja:
    @staticmethod
    def abrir(jogador):
        print("\n=== Mercador da vila ===")
        while True:
            print(f"Ouro: {jogador.ouro} PO\n")
            for i, item in enumerate(ITENS_LOJA):
                print(f"  [{i}] {item.descricao()}")
            print(f"  [{len(ITENS_LOJA)}] Sair")
            try:
                opc = int(input("Comprar: "))
            except ValueError:
                continue
            if opc == len(ITENS_LOJA):
                return
            if 0 <= opc < len(ITENS_LOJA):
                item = ITENS_LOJA[opc]
                if jogador.ouro < item.valor:
                    print("Ouro insuficiente.")
                    continue
                if item.tipo == "consumivel":
                    jogador.ouro -= item.valor
                    from sistema.dados import rolar

                    cura = rolar("2d4") + 2
                    jogador.hp = min(jogador.hp_max, jogador.hp + cura)
                    print(f"Poção usada! +{cura} HP.")
                else:
                    jogador.ouro -= item.valor
                    novo = Equipamento(
                        item.nome,
                        dano=item.dano,
                        dado_dano=item.dado_dano,
                        valor=item.valor,
                        agilidade=item.agilidade,
                        bonus_ca=item.bonus_ca,
                        tipo=item.tipo,
                    )
                    jogador.add_item_inventario(novo)
