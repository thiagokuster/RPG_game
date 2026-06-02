CLASSES = {
    "guerreiro": {
        "nome": "Guerreiro",
        "dado_vida": 10,
        "atributo_principal": "forca",
        "proficiencia_combate": True,
        "magia": False,
    },
    "ladino": {
        "nome": "Ladino",
        "dado_vida": 8,
        "atributo_principal": "destreza",
        "proficiencia_combate": True,
        "magia": False,
    },
    "mago": {
        "nome": "Mago",
        "dado_vida": 6,
        "atributo_principal": "inteligencia",
        "proficiencia_combate": False,
        "magia": True,
        "trouxas": 3,
    },
    "clerigo": {
        "nome": "Clérigo",
        "dado_vida": 8,
        "atributo_principal": "sabedoria",
        "proficiencia_combate": False,
        "magia": True,
        "trouxas": 2,
    },
}


def escolher_classe() -> str:
    opcoes = list(CLASSES.keys())
    print("\n=== Escolha sua classe ===")
    for i, chave in enumerate(opcoes, 1):
        info = CLASSES[chave]
        print(f"  [{i}] {info['nome']} (d{info['dado_vida']} de vida)")
    while True:
        try:
            escolha = int(input("Classe: ")) - 1
            if 0 <= escolha < len(opcoes):
                return opcoes[escolha]
        except ValueError:
            pass
        print("Opção inválida.")
