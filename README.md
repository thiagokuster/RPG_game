# Arena RPG (Python)

Jogo de arena PvP em terminal, inspirado nas regras da **D&D 5ª Edição** ([Livro do Jogador](https://ordempendragon.wordpress.com/wp-content/uploads/2017/04/dd-5e-livro-do-jogador-fundo-branco-biblioteca-c3a9lfica.pdf)). Versão quase final com criação de personagem, combate por iniciativa, progressão e economia.

## Como jogar

```bash
python main.py
```

Requisitos: Python 3.10+

## O que o jogo inclui

### Criação de personagem
- **Seis atributos** (Força, Destreza, Constituição, Inteligência, Sabedoria, Carisma) com modificadores no estilo 5e: `(valor - 10) // 2`
- Geração **padrão** (15, 14, 13, 12, 10, 8) ou **aleatória** (4d6, descarta o menor)
- **Quatro classes**: Guerreiro, Ladino, Mago, Clérigo — cada uma com dado de vida, atributo principal e regras próprias

### Combate
- **Iniciativa**: `1d20 + modificador de Destreza`
- **Ataque**: `1d20 + bônus` contra **Classe de Armadura (CA)** do alvo
- **Crítico** no 20 natural (dobra dados de dano); **falha crítica** no 1
- Dano com **dados de arma** (`1d8`, `1d12`, etc.) + modificador do atributo principal
- **Magias** para Mago e Clérigo (raio arcano, cura; trouxas limitadas)
- XP e ouro ao derrotar oponentes; **subida de nível** com mais HP

### Equipamento e economia
- Armas, armaduras e anéis com bônus de CA e ataque
- **Loja** com poções, armaduras e armas em peças de ouro (PO)
- Inventário com equipar/desequipar

### Partida
- 2 a 6 jogadores em turnos por rodada
- **Descanso curto** (`1d8 + CON`) e **descanso longo** automático a cada 3 rodadas
- Vitória quando resta um aventureiro de pé

## Estrutura do projeto

```
RPG/
├── main.py              # Loop principal e menu
├── sistema/             # Regras D&D (dados, atributos, classes)
├── jogador/             # Ficha e ações do personagem
├── combate/             # Ataques e magias em combate
├── equipamento/         # Itens e armaduras
├── partida/             # Rodadas, morte, vitória
└── loja/                # Mercador
```

## Próximos passos (ideias)

- Modo PvE com monstros e masmorras
- Perícias e testes de habilidade (`1d20 + mod`)
- Mais magias e subclasses
- Salvar/carregar partida

## Licença

Projeto educacional. D&D é marca da Wizards of the Coast; este jogo é uma implementação caseira inspirada nas regras, sem afiliação oficial.
