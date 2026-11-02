from time import sleep
from random import randint

from equipamento import Equipamento
from jogador import Jogador


class Loja:

    def __init__(self, popular=True):
        self.estoque: list[Equipamento] = []
        self.slot = 3
        self.preco_slot = 3
        self.turno = 1
        if popular:
            self.att_loja(anunciar=False)

    def entrar_loja(self, jog: Jogador):
        while True:
            self.mostrar_loja(jog)
            if not self.compra(jog):
                break

    def tem_moeda(self, jog: Jogador, valor):
        if jog.moedas < valor:
            print("Moedas insuficiente!")
            return False

        jog.moedas -= valor
        return True

    def novo_equip(self, tipo=None):
        if tipo:
            equip = Equipamento.gerar_por_categoria(self.turno, tipo)
        else:
            equip = Equipamento.gerarEquipamento(self.turno)
        self.estoque.append(equip)

    def att_loja(self, anunciar=True):
        if anunciar:
            print("Loja Atualizada!")
            sleep(0.6)
        self.estoque = Equipamento.gerar_estoque(self.turno, self.slot)

    def chance_att_loja(self):
        fim = 3
        if self.turno == 20:
            print("50% de chance da loja atualizar!")
            sleep(1)
        if self.turno >= 20:
            fim = 2
        chance = randint(1, fim)
        if chance == 1:
            self.att_loja()
        return

    def _por_categoria(self):
        grupos = {"arma": [], "armadura": [], "anel": []}
        for item in self.estoque:
            grupos.setdefault(item.tipo or "arma", []).append(item)
        return grupos

    def mostrar_loja(self, jog: Jogador):
        print("\n=== LOJA ===")
        if self.estoque:
            titulos = {"arma": "ARMAS", "armadura": "ARMADURAS", "anel": "ACESSORIOS"}
            grupos = self._por_categoria()
            for tipo in ("arma", "armadura", "anel"):
                itens = grupos.get(tipo) or []
                if not itens:
                    continue
                print(f"-- {titulos[tipo]} --")
                for item in itens:
                    indice = self.estoque.index(item)
                    print(f"[{indice}] {item.descricao()}")
        else:
            print("Nenhum equipamento disponivel na loja!")
            sleep(1)
        print("-=" * 30)
        print(f"[-3] Comprar +1 slot ({self.preco_slot} moedas)")
        print(f"[-2] Atualizar a loja (5 moedas)")
        print(f"[-1] Sair")
        print(f"Suas moedas: {jog.moedas}")

    def compra(self, jog: Jogador):
        while True:
            try:
                indice = int(input("Sua opcao : "))
                if indice in [-3, -2, -1]:
                    break
                if 0 <= indice < len(self.estoque):
                    break
                print("Opcao invalida")
            except ValueError:
                print("Digite um valor valido")
        if indice == -1:
            return False
        elif indice == -2:
            if self.tem_moeda(jog, 5):
                self.att_loja()
        elif indice == -3:
            if self.tem_moeda(jog, self.preco_slot):
                self.slot += 1
                self.preco_slot += 2
                self.novo_equip()
        else:
            if self.tem_moeda(jog, self.estoque[indice].valor):
                jog.adicionar_item_inventario(self.estoque[indice])
                self.estoque.remove(self.estoque[indice])
        return True
