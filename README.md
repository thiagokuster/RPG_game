# Arena RPG 5e

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Status-Playable-success?style=for-the-badge" alt="Playable" />
  <img src="https://img.shields.io/badge/Mode-Terminal-000000?style=for-the-badge" alt="Terminal" />
</p>

Um jogo de RPG em terminal inspirado em fantasia medieval, com turnos de combate, classes, magia, monstros aleatórios, loja, inventário e progressão de personagem.

## Índice

- [Visão geral](#visão-geral)
- [Como jogar](#como-jogar)
- [Classes](#classes)
- [Como executar](#como-executar)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Testes](#testes)
- [Licença](#licença)

## Visão geral

Arena RPG 5e é um projeto simples, divertido e fácil de executar em terminal. A partida é jogada por turnos e pode se desenvolver de várias formas:

- um único jogador sobrevive e vence a partida
- todos os jogadores morrem e a partida termina sem vencedor
- monstros aleatórios podem mudar completamente o rumo da batalha

O foco é manter partidas tensas, rápidas de entender e interessantes para grupos de jogadores.

## Como jogar

### 1. Início da partida

Ao iniciar o jogo, o programa pergunta quantos jogadores participarão. O mínimo é 2.

### 2. Escolha da classe

Cada jogador escolhe uma classe antes da partida começar:

- [1] Guerreiro
- [2] Mago
- [3] Arqueiro
- [4] Paladino
- [5] Clerigo

### 3. Menu principal

A cada turno, o jogador atual verá as opções:

- [1] Atacar
- [2] Loja
- [3] Inventário

### 4. Sistema de combate

Ao escolher atacar:

- o jogo mostra os alvos disponíveis
- você deve escolher um alvo diferente de si mesmo
- o ataque usa d20 + bônus de ataque + proficiência
- se o valor total for menor que a CA do alvo, o ataque falha
- em caso de acerto, o dano é calculado e pode criticar em 20 natural

### 5. Loja e inventário

Na loja, os jogadores podem:

- comprar itens do estoque
- atualizar a loja
- comprar mais espaço para o inventário

No inventário, é possível ver todos os itens adquiridos e equipá-los quando fizer sentido.

### 6. Monstros e eventos aleatórios

Em algumas rodadas, um monstro pode aparecer e surpreender o jogador atual. Quando isso acontece, a luta continua até que alguém seja derrotado.

Se o monstro for vencido, o jogador recebe recompensas e experiência.

### 7. Condição de vitória

A partida termina quando:

- resta apenas um jogador vivo → esse jogador vence
- todos os jogadores morrem → não há vencedor

### 8. Dicas rápidas

- conserve vida quando possível
- aproveite a loja no momento certo
- classes com magia podem mudar completamente o rumo da partida
- partidas com mais jogadores costumam durar mais e serem mais emocionantes

## Classes

| Classe | Estilo | Vantagem principal |
| --- | --- | --- |
| Guerreiro | Força e resistência | Muito HP e dano consistente |
| Mago | Magia ofensiva | Dano mágico e cura |
| Arqueiro | Precisão | Ataques ágeis e efetivos |
| Paladino | Equilíbrio | Defesa e apoio |
| Clerigo | Cura e suporte | Recuperação e magia utilitária |

## Como executar

### Windows / PowerShell

```powershell
cd "D:\Meus Trabalhos\Projetos\RPG"
python main.py
```

### Linux / macOS

```bash
cd /caminho/para/o/projeto
python main.py
```

Se o comando `python` não funcionar, tente:

```bash
python3 main.py
```

## Estrutura do projeto

```text
RPG/
├── main.py
├── README.md
├── LICENSE
├── .gitignore
├── tests/
│   ├── test_combate.py
│   └── test_sistema_avancado.py
├── combate/
│   ├── __init__.py
│   └── combate.py
├── equipamento/
│   ├── __init__.py
│   └── equipamento.py
├── jogador/
│   ├── __init__.py
│   └── jogador.py
├── loja/
│   ├── __init__.py
│   └── loja.py
├── magia/
│   ├── __init__.py
│   └── magia.py
├── monstro/
│   ├── __init__.py
│   └── monstro.py
├── partida/
│   ├── __init__.py
│   └── partida.py
└── ...
```

## Testes

Para validar o funcionamento do jogo, execute:

```bash
python -m unittest discover -s tests -v
```

## Licença

Este projeto está distribuído sob a licença MIT.

## Autor

Projeto desenvolvido em Python como estudo de lógica de RPG, combate por turno e estrutura de jogo em terminal.
