class Jogador :
    def __init__(self,nome,hp):
        self.nome = nome
        self.hp = hp
        self.danobase = 0
        self.agilidadebase = 0
        self.inventario = []

        #slots
        self.arma = None
        self.anel = None

    def add_item_inventario(self,item) :
        print(f"{item.nome} foi adicionado ao inventario")
        self.inventario.append(item)

    def mostrar_inventario(self) :
        if not self.inventario :
            print("Inventario vazio")
            return
        opc = 0
        fim = len(self.inventario)
        while opc != fim :
 
            for i, item in enumerate(self.inventario) :
                print(f"-[{i}] {item.nome} dano : {item.dano} agilidade : {item.agilidade}")
            print(f"- [{len(self.inventario)}] Saida")
            if self.arma :  
                print(f"Arma equipada : {self.arma.nome}")
            if self.anel :
                print(f"Anel equipada : {self.anel.nome}")
            opc = int (input ("> ")) 
            if opc == fim :
                return
            if self.inventario[opc].tipo == "arma" or self.inventario[opc].tipo == "anel" :
                self.equipar(self.inventario[opc]) 

    def equipar(self,item): 
        if item not in self.inventario :
            print(f"{item.nome} Nao esta no inventario")
            return
        if item.tipo == 'arma' :
            if self.arma : 
                print(f"Desequipando {self.arma.nome}")
            self.arma = item
        elif item.tipo == 'anel' :
            if self.anel : 
                print(f"Desequipando {self.anel.nome}")
            self.anel = item
        print(f"{self.nome} Equipou {item.nome}")

class Equipamento :
    def __init__(self,nome,dano=0,valor=0,agilidade=0,tipo=None):
        self.nome = nome
        self.dano = dano
        self.valor = valor
        self.agilidade = agilidade
        self.tipo = tipo


qj = int(input("Quantos jogadores teremos na partida ? "))

jogadores : list[Jogador] = []
hp = int(input("Hp dos jogadores : "))

for i in range(qj) :
    nome = str(input(f"Nome do jogador {i+1} "))
    jogadores.append(Jogador(nome,hp))

jogadoratual = 0
espada = Equipamento(nome = "Espada de pedra", dano = 5 , valor = 8, agilidade = 0, tipo = "arma")
espada2 = Equipamento(nome = "Faca", dano = 3 , valor = 6, agilidade = 2, tipo = "arma")
anel = Equipamento(nome = "Anel de velocidade", dano = 1 , valor = 6, agilidade = 4, tipo = "anel")
anel2 = Equipamento(nome = "Anel de forca", dano = 2 , valor = 8, agilidade = 3, tipo = "anel")
jogadores[0].add_item_inventario(espada)
jogadores[0].equipar(espada)


while True :
    print(f"""
    vez do jogador {jogadores[jogadoratual].nome}
    [1] Atacar
    [2] Loja
    [3] Ver inventario
    """)

    opc = int (input ("Sua opcao : "))

    if opc == 1 :
        if qj > 2:
            for i in range(qj):
                if i != jogadoratual :
                    print(f"- [{i}] {jogadores[i].nome}")
            alvo = int (input ("Escolha quem voce vai atacar"))
        else :
            for i in range (qj) :
                if i != jogadoratual :
                    alvo = i
        print(f"{jogadores[jogadoratual].nome} Atacou {jogadores[alvo].nome}")
        jogadoratual = (jogadoratual + 1) % qj 

    if opc == 2 :
        pass

    if opc == 3 :
        jogadores[jogadoratual].mostrar_inventario() 