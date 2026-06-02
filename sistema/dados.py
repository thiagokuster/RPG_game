from random import randint


def rolar(dado: str) -> int:
    """Rola dados no formato D&D (ex: '1d20', '2d6+3')."""
    expressao = dado.replace(" ", "").lower()
    bonus = 0
    if "+" in expressao:
        expressao, extra = expressao.split("+", 1)
        bonus = int(extra)
    elif "-" in expressao and "d" not in expressao.split("-", 1)[0]:
        expressao, extra = expressao.split("-", 1)
        bonus = -int(extra)

    if "d" not in expressao:
        return int(expressao) + bonus

    qtd, faces = expressao.split("d", 1)
    qtd = int(qtd) if qtd else 1
    faces = int(faces)
    total = sum(randint(1, faces) for _ in range(qtd))
    return total + bonus


def modificador(valor: int) -> int:
    """Modificador de atributo conforme Livro do Jogador D&D 5e."""
    return (valor - 10) // 2
