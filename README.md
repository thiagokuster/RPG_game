# Arena RPG 5e

RPG de arena por turnos, no estilo 5e, para partidas locais entre amigos. Dá para jogar no terminal, no lobby web ou por TCP na mesma rede.

## 🚀 Demo

Não há deploy público. A partida roda na sua máquina ou na rede interna:

- Lobby web: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Servidor TCP: `127.0.0.1:5000`

## 🛠️ Tecnologias

- Python 3.10+ (biblioteca padrão)
- HTTP + SSE para o lobby web
- HTML, CSS e JavaScript no frontend
- TCP com mensagens JSON para o modo online
- `unittest` para os testes

## ✨ Funcionalidades

- Cinco classes: Guerreiro, Mago, Arqueiro, Paladino e Clérigo
- Combate por turnos com ataque, magia, loja e inventário
- Armadura com redução de dano e durabilidade
- Eventos aleatórios (tesouro, aposta, risco e monstros)
- Lobby web com salas, senha opcional e no máximo 6 jogadores
- Sessão por token: só o anfitrião inicia, e cada jogador age pela própria identidade
- Servidor TCP com reconexão após reinício
- Partida no terminal para um grupo no mesmo computador

## 📦 Como rodar localmente

```bash
git clone https://github.com/thiagokuster/RPG_game.git
cd RPG_game
```

Não precisa instalar dependências extras. Use o Python 3.10 ou superior.

### Lobby web (recomendado para amigos)

```bash
python private_site.py --host 127.0.0.1 --port 8000
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000), crie a sala, compartilhe o código e inicie quando houver pelo menos dois jogadores.

Na rede interna, use `--host 0.0.0.0` só em rede confiável. Os outros acessam `http://SEU_IP:8000`.

### Terminal

```bash
python main.py
```

### Servidor TCP

```bash
python private_server.py --host 127.0.0.1 --port 5000
```

Em outro terminal, para cada jogador:

```bash
python private_client.py --host 127.0.0.1 --port 5000 --player NomeDoJogador --room Sala1
```

### Testes

```bash
python -m unittest discover -s tests -q
```
