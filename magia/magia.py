from dataclasses import dataclass


@dataclass
class Magia:
    nome: str
    tipo: str
    dano: int = 0
    cura: int = 0
    custo: int = 1
    descricao: str = ""

    @classmethod
    def bola_de_fogo(cls):
        return cls(
            nome="Bola de Fogo",
            tipo="dano",
            dano=18,
            custo=2,
            descricao="Explosão arcana que causa dano ao alvo.",
        )

    @classmethod
    def cura_leve(cls):
        return cls(
            nome="Cura Leve",
            tipo="cura",
            cura=15,
            custo=1,
            descricao="Restaura vida do alvo.",
        )

    @classmethod
    def rajada_congelante(cls):
        return cls(
            nome="Rajada Congelante",
            tipo="dano",
            dano=12,
            custo=2,
            descricao="Cone de gelo que afeta o alvo.",
        )

    @classmethod
    def golpe_de_energia(cls):
        return cls(
            nome="Golpe de Energia",
            tipo="dano",
            dano=14,
            custo=2,
            descricao="Ataque místico poderoso para causar dano.",
        )
