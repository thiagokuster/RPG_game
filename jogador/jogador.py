from random import randint
from time import sleep

from equipamento import Equipamento
from sistema.dados import rolar, modificador
from sistema.atributos import ATRIBUTOS, gerar_atributos
from sistema.classes_rpg import CLASSES


class Jogador:
    def __init__(self, nome: str, classe: str, atributos: dict[str, int] | None = None):
        self.nome = nome
        self.classe = classe
        info = CLASSES[classe]
        self.nivel = 1
        self.xp = 0
        self.ouro = 50
        self.inventario: list[Equipamento] = []
        self.arma: Equipamento | None = None
        self.armadura: Equipamento | None = None
        self.anel: Equipamento | None = None
        self.trouxas_magia = info.get("trouxas", 0)

        self.atributos = atributos or gerar_atributos()
        mod_con = modificador(self.atributos["constituicao"])
        dado_vida = info["dado_vida"]
        self.hp_max = dado_vida + mod_con
        self.hp = self.hp_max
        self.ca = self._calcular_ca()

    def _calcular_ca(self) -> int:
        mod_des = modificador(self.atributos["destreza"])
        ca = 10 + mod_des
        if self.armadura:
            ca += self.armadura.bonus_ca
            if self.armadura.agilidade:
                ca += min(mod_des, self.armadura.agilidade)
        if self.anel and self.anel.bonus_ca:
            ca += self.anel.bonus_ca
        return ca

    def modificador_principal(self) -> int:
        attr = CLASSES[self.classe]["atributo_principal"]
        return modificador(self.atributos[attr])

    def bonus_proficiencia(self) -> int:
        return 2 + (self.nivel - 1) // 4

    def bonus_ataque(self) -> int:
        bonus = self.modificador_principal()
        if CLASSES[self.classe]["proficiencia_combate"]:
            bonus += self.bonus_proficiencia()
        if self.arma and self.arma.agilidade:
            bonus += self.arma.agilidade
        return bonus

    def rolar_iniciativa(self) -> int:
        return rolar("1d20") + modificador(self.atributos["destreza"])

    def rolar_d20(self, rotulo: str = "Teste") -> int:
        print(f"Rolando {rotulo}...")
        sleep(0.3)
        resultado = rolar("1d20")
        print(f"  → {resultado}")
        return resultado

    def calcular_dano(self, critico: bool = False) -> int:
        total = self.modificador_principal()
        if self.arma:
            if self.arma.dado_dano:
                vezes = 2 if critico else 1
                for _ in range(vezes):
                    total += rolar(self.arma.dado_dano)
            else:
                total += self.arma.dano * (2 if critico else 1)
        return max(1, total)

    def descanso_curto(self):
        cura = rolar("1d8") + modificador(self.atributos["constituicao"])
        self.hp = min(self.hp_max, self.hp + max(1, cura))
        print(f"{self.nome} recupera {cura} HP (descanso curto).")

    def descanso_longo(self):
        self.hp = self.hp_max
        if self.trouxas_magia:
            info = CLASSES[self.classe]
            self.trouxas_magia = info.get("trouxas", self.trouxas_magia)
        print(f"{self.nome} descansou e está em plena forma.")

    def ganhar_xp(self, quantidade: int):
        self.xp += quantidade
        necessario = self.nivel * 100
        if self.xp >= necessario:
            self.subir_nivel()

    def subir_nivel(self):
        self.nivel += 1
        self.xp = 0
        info = CLASSES[self.classe]
        mod_con = modificador(self.atributos["constituicao"])
        ganho = max(1, rolar(f"1d{info['dado_vida']}") + mod_con)
        self.hp_max += ganho
        self.hp = self.hp_max
        print(f"\n*** {self.nome} subiu para o nível {self.nivel}! (+{ganho} HP máx) ***\n")

    def status(self) -> str:
        return (
            f"{self.nome} | {CLASSES[self.classe]['nome']} nv.{self.nivel} | "
            f"HP {self.hp}/{self.hp_max} | CA {self.ca} | {self.ouro} PO | XP {self.xp}"
        )

    def mostrar_ficha(self):
        print(f"\n--- Ficha: {self.nome} ({CLASSES[self.classe]['nome']}) ---")
        for attr in ATRIBUTOS:
            val = self.atributos[attr]
            mod = modificador(val)
            sinal = "+" if mod >= 0 else ""
            print(f"  {attr.capitalize():14} {val:2} ({sinal}{mod})")
        print(f"  CA: {self.ca}  |  Ataque: +{self.bonus_ataque()}")
        if self.trouxas_magia:
            print(f"  Trouxas de magia: {self.trouxas_magia}")
        print(self.status())

    def add_item_inventario(self, item: Equipamento):
        print(f"{item.nome} adicionado ao inventário.")
        self.inventario.append(item)

    def equipar(self, item: Equipamento):
        if item not in self.inventario:
            print(f"{item.nome} não está no inventário.")
            return
        if item.tipo == "arma":
            if self.arma:
                print(f"Desequipando {self.arma.nome}.")
            self.arma = item
        elif item.tipo == "armadura":
            if self.armadura:
                print(f"Desequipando {self.armadura.nome}.")
            self.armadura = item
        elif item.tipo == "anel":
            if self.anel:
                print(f"Desequipando {self.anel.nome}.")
            self.anel = item
        else:
            print("Item não equipável.")
            return
        self.ca = self._calcular_ca()
        print(f"{self.nome} equipou {item.nome}. CA atual: {self.ca}")

    def conjurar_magia(self, alvo: "Jogador") -> bool:
        info = CLASSES[self.classe]
        if not info.get("magia"):
            print("Sua classe não conjura magias.")
            return False
        if self.trouxas_magia <= 0:
            print("Sem trouxas de magia restantes.")
            return False

        attr = info["atributo_principal"]
        cd = 8 + self.bonus_proficiencia() + modificador(self.atributos[attr])
        print("\nMagias: [1] Raio arcano (1d10)  [2] Curar ferimentos (1d8+mod)")
        try:
            escolha = int(input("Magia: "))
        except ValueError:
            return False

        self.trouxas_magia -= 1
        if escolha == 2:
            cura = rolar("1d8") + modificador(self.atributos[attr])
            self.hp = min(self.hp_max, self.hp + cura)
            print(f"{self.nome} se curou em {cura} HP.")
            return True

        ataque_magico = rolar("1d20") + self.bonus_proficiencia() + modificador(self.atributos[attr])
        print(f"Ataque mágico: {ataque_magico} vs CA {alvo.ca}")
        if ataque_magico >= alvo.ca:
            dano = rolar("1d10") + modificador(self.atributos[attr])
            alvo.hp -= dano
            print(f"{alvo.nome} sofreu {dano} de dano mágico!")
            return True
        print("A magia falhou contra a CA do alvo.")
        return False

    def mostrar_inventario(self):
        if not self.inventario:
            print("Inventário vazio.")
            return
        while True:
            for i, item in enumerate(self.inventario):
                print(f"  [{i}] {item.descricao()}")
            print(f"  [{len(self.inventario)}] Voltar")
            if self.arma:
                print(f"  Arma: {self.arma.nome}")
            if self.armadura:
                print(f"  Armadura: {self.armadura.nome}")
            if self.anel:
                print(f"  Anel: {self.anel.nome}")
            try:
                opc = int(input("> "))
            except ValueError:
                continue
            if opc == len(self.inventario):
                return
            if 0 <= opc < len(self.inventario):
                item = self.inventario[opc]
                if item.tipo in ("arma", "armadura", "anel"):
                    self.equipar(item)

    @classmethod
    def criar(cls, indice: int) -> "Jogador":
        from sistema.classes_rpg import escolher_classe

        nome = input(f"Nome do jogador {indice + 1}: ").strip() or f"Aventureiro {indice + 1}"
        print("\nAtributos: [1] Padrão (15,14,13,12,10,8)  [2] Aleatório (4d6)")
        metodo = "aleatorio" if input("Método: ").strip() == "2" else "padrao"
        atributos = gerar_atributos(metodo)
        print("\nDistribua os valores (maior costuma ir no atributo principal da classe):")
        for i, attr in enumerate(ATRIBUTOS, 1):
            print(f"  [{i}] {attr.capitalize()}")
        valores = list(atributos.values())
        distribuido: dict[str, int] = {}
        for attr in ATRIBUTOS:
            print(f"\nAtributo para {attr}? Valores restantes: {valores}")
            while True:
                try:
                    escolha = int(input("Número: ")) - 1
                    if 0 <= escolha < len(valores):
                        distribuido[attr] = valores.pop(escolha)
                        break
                except ValueError:
                    pass
        print("\nEscolha a classe:")
        classe = escolher_classe()
        jogador = cls(nome, classe, distribuido)
        jogador.mostrar_ficha()
        return jogador
