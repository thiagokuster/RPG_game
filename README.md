# Arena RPG

Jogo de RPG em terminal, inspirado nas regras de D&D e em jogos de arena, com combate por turno, loja, inventário e sistema de sobrevivência.

## 🚀 Demo

Este projeto é executado localmente no terminal, sem deploy web.

## 🛠️ Tecnologias

- Python 3
- Programação orientada a objetos
- Estruturas de dados em lista
- Lógica de turnos e combate
- Terminal/console para interação do jogador

## ✨ Funcionalidades

- Partida com 2 ou mais jogadores
- Sistema de turnos por jogador
- Ataque com dados aleatórios
- Loja com itens e upgrades
- Inventário com equipamentos e arma equipável
- Sistema de eliminação e vitória
- Geração aleatória de itens raros
- Progressão por moedas e sobrevivência

## 📦 Como rodar localmente

1. Clone o repositório e entre na pasta:

```bash
git clone https://github.com/thiagokuster/RPG_game.git
cd RPG_game
```

2. Verifique se o Python está instalado:

```bash
python --version
```

3. Execute o jogo:

```bash
python main.py
```

## 🎮 Como jogar

1. O programa solicita a quantidade de jogadores da partida.
2. Digite um número maior que 1 para iniciar.
3. Cada jogador começa com 100 de vida.
4. No menu principal, escolha uma opção:
   - 1: Atacar
   - 2: Loja
   - 3: Inventário
5. Em combate, cada jogador escolhe um alvo e tenta acertar o ataque.
6. Se o ataque acertar, o alvo perde HP.
7. Quando um jogador chega a 0 de HP, ele é eliminado.
8. O vencedor é o último jogador restante vivo.
9. Na loja, é possível comprar itens, atualizar o estoque e aumentar a quantidade de slots.
10. Itens comprados vão para o inventário e podem ser equipados.

## 📋 Regras básicas

- Cada turno, um jogador realiza sua ação.
- O dano depende do dado, do bônus base e da arma equipada.
- Ataque especial acontece quando o dado de agilidade chega a 20.
- O jogador pode ganhar moedas ao longo da partida.
- A partida termina quando sobra apenas um jogador vivo.

## 🧩 Estrutura do projeto

```text
RPG/
├── main.py
├── README.md
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
├── partida/
│   ├── __init__.py
│   └── partida.py
└── ...
```

## 📝 Observações

- O jogo é totalmente executado no terminal, sem interface gráfica.
- O objetivo principal é praticar lógica de RPG, classes em Python e fluxo de jogo.
- O projeto pode ser expandido com novos itens, monstros, mapas, classes de personagens e mais mecânicas.

## 👤 Autor

Projeto desenvolvido como estudo de Python e lógica de jogos em RPG.
