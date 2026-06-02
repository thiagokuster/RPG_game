from random import randint

ATRIBUTOS = ("forca", "destreza", "constituicao", "inteligencia", "sabedoria", "carisma")


def gerar_atributos(metodo: str = "padrao") -> dict[str, int]:
    """
    Gera os seis atributos do personagem.
    padrao: array 15,14,13,12,10,8 (estilo point-buy simplificado)
    aleatorio: 4d6 descarta o menor, seis vezes
    """
    if metodo == "aleatorio":
        valores = []
        for _ in range(6):
            rolagens = sorted(randint(1, 6) for _ in range(4))
            valores.append(sum(rolagens[1:]))
        valores.sort(reverse=True)
    else:
        valores = [15, 14, 13, 12, 10, 8]

    return dict(zip(ATRIBUTOS, valores))
