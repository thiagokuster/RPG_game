from random import randint

from equipamento import Equipamento
from jogador import Jogador
from motor.eventos import evento, nome


class Loja:
    def __init__(self, popular=True):
        self.estoque: list[Equipamento] = []
        self.slot = 3
        self.preco_slot = 3
        self.turno = 1
        if popular:
            self.att_loja()

    def tem_moeda(self, jog: Jogador, valor):
        if jog.moedas < valor:
            return False
        jog.moedas -= valor
        return True

    def novo_equip(self, tipo=None):
        if tipo:
            equip = Equipamento.gerar_por_categoria(self.turno, tipo)
        else:
            equip = Equipamento.gerarEquipamento(self.turno)
        self.estoque.append(equip)
        return equip

    def att_loja(self, anunciar=True):
        self.estoque = Equipamento.gerar_estoque(self.turno, self.slot)
        return list(self.estoque)

    def chance_att_loja(self):
        fim = 2 if self.turno >= 20 else 3
        chance = randint(1, fim)
        if chance == 1:
            self.att_loja()
            return True
        return False

    def _por_categoria(self):
        grupos = {"arma": [], "armadura": [], "anel": []}
        for item in self.estoque:
            grupos.setdefault(item.tipo or "arma", []).append(item)
        return grupos

    def catalogo(self):
        return list(self.estoque)

    def comprar(self, jog: Jogador, indice):
        if indice == -2:
            if not self.tem_moeda(jog, 5):
                return evento("erro", motivo="Moedas insuficientes.")
            self.att_loja()
            return evento("loja", de=nome(jog), resultado="atualizar")
        if indice == -3:
            if not self.tem_moeda(jog, self.preco_slot):
                return evento("erro", motivo="Moedas insuficientes.")
            self.slot += 1
            self.preco_slot += 2
            item = self.novo_equip()
            return evento("loja", de=nome(jog), resultado="slot", item=item.nome)
        if not 0 <= indice < len(self.estoque):
            return evento("erro", motivo="Item inválido.")
        item = self.estoque[indice]
        if not self.tem_moeda(jog, item.valor):
            return evento("erro", motivo="Moedas insuficientes.")
        jog.adicionar_item_inventario(item)
        self.estoque.remove(item)
        return evento("loja", de=nome(jog), resultado="compra", item=item.nome)

    def entrar_loja(self, jog: Jogador):
        from ui.terminal import loop_loja

        loop_loja(self, jog)
