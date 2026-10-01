from random import randint
from time import sleep 
from equipamento import Equipamento 
class Jogador :
    def __init__(self,nome,hp):
        self.nome = nome
        self.hp = hp
        self.danobase=10 
        self.agilidadebase=0
        self.moedas=0
        self.inventario = []


        self.arma:Equipamento = None
        self.anel = None

    def d10(self):
        print("Rolando dado de ataque...")
        sleep(0.5)
        resultado = randint(1, 10)
        print(resultado)
        return resultado
    
    def d20(self):
        print("Rolando dado de agilidade...")
        sleep(0.5)
        resultado = randint(1, 20)
        print(resultado)
        return resultado

    def danotot(self,d10,d20):
        danotot = d10
        if self.danobase >0 :
            print(f"+ {self.danobase} de bonus")
            danotot += self.danobase
        if self.arma and self.arma.dano > 0 :
            danotot += self.arma.dano
            print(f"+ {self.arma.dano}")
        if d20 >= 20 :
            print("ATAQUE ESPECIAL!!!")
            sleep(0.3)
            danotot *= 2
        return danotot


    def adicionar_item_inventario(self, item):
        print(f"{item.nome} foi adicionado no inventario")
        self.inventario.append(item)

    def mostrar_inventario(self):
        if not self.inventario:
            print("Inventario vazio")
            return

        fim = len(self.inventario)
        while True:
            from partida import Partida
            print("=== INVENTARIO ===")
            for i, item in enumerate(self.inventario):
                print(f"-[{i}] {item.nome} - dano: {item.dano} agilidade: {item.agilidade} tipo: {item.tipo}")
            print(f"-[{fim}] Saida")
            if self.arma:
                print(f"Arma equipada : {self.arma.nome}")
            if self.anel:
                print(f"Anel equipado : {self.anel.nome}")

            opc = Partida.validar_opc(list(range(fim + 1)), "Escolha um item do inventario: ")
            if opc is None or opc == fim:
                return
            item = self.inventario[opc]
            if item.tipo in ["arma", "anel"]:
                self.equipar(item)
            else:
                print(f"{item.nome} nao pode ser equipado")
            break

    def equipar(self,item):
        if item not in self.inventario :
            print(f"{item.nome} nao esta no inventario")
            return
        if item.tipo == 'arma':
            if self.arma:
                print(f"Desequipando {self.arma.nome}")
            self.arma = item
        elif item.tipo == 'anel':
            if self.anel:
                print(f"Desequipando {self.anel.nome}")
            self.anel = item
        print(f"{self.nome} equipou {item.nome}")

