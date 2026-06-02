class Equipamento:
    def __init__(
        self,
        nome,
        dano=0,
        dado_dano="",
        valor=0,
        agilidade=0,
        bonus_ca=0,
        tipo=None,
    ):
        self.nome = nome
        self.dano = dano
        self.dado_dano = dado_dano
        self.valor = valor
        self.agilidade = agilidade
        self.bonus_ca = bonus_ca
        self.tipo = tipo

    def descricao(self) -> str:
        dano_txt = self.dado_dano or str(self.dano)
        extras = []
        if self.bonus_ca:
            extras.append(f"CA +{self.bonus_ca}")
        if self.agilidade:
            extras.append(f"DES +{self.agilidade}")
        extra = f" ({', '.join(extras)})" if extras else ""
        return f"{self.nome} [{self.tipo}] dano {dano_txt}{extra} — {self.valor} PO"
