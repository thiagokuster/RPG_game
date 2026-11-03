from random import randint

from combate import resolver_ataque
from eventos import gerar_evento, resolver_evento
from jogador import Jogador
from motor.eventos import evento, nome, textos


class Partida:
    ONDAS_MAX = 3

    def __init__(self, jogadores: list[Jogador], modo="pvp"):
        self.jogadores = jogadores
        self.mortos = []
        self.modo = modo
        self.onda = 0
        self.seq = 0
        self.eventos = []
        for jogador in jogadores:
            if getattr(jogador, "tipo", "") == "chefe":
                self.onda = max(self.onda, getattr(jogador, "onda", 1))

    def vivos(self):
        return [jogador for jogador in self.jogadores if jogador.hp > 0]

    def vivos_jogadores(self):
        return [jogador for jogador in self.vivos() if getattr(jogador, "classe", "") not in {"chefe", "bestia", "humanoide", "undead", "monstro"}]

    def proximo_vivo(self, atual):
        vivos = self.vivos()
        if self.modo == "coop":
            if not self.vivos_jogadores():
                return None
            monstros = [j for j in vivos if j not in self.vivos_jogadores()]
            if not monstros:
                return None
        elif len(vivos) <= 1:
            return None
        if atual not in self.jogadores:
            return vivos[0]
        indice = self.jogadores.index(atual)
        total = len(self.jogadores)
        for passo in range(1, total + 1):
            candidato = self.jogadores[(indice + passo) % total]
            if candidato.hp > 0:
                return candidato
        return None

    @classmethod
    def registrar_jogadores(cls, qj, hp=100, classes=None):
        nomes = [f"Jogador {i + 1}" for i in range(qj)]
        passivas = {nomes[i]: classes[i] for i in range(min(len(nomes), len(classes or [])))} or None
        return Jogador.criar_elenco(nomes, passivas)

    def carimbar(self, eventos):
        saida = []
        for ev in eventos or []:
            if not isinstance(ev, dict):
                continue
            dado = dict(ev)
            if "id" not in dado:
                self.seq += 1
                dado["id"] = self.seq
            saida.append(dado)
        self.registrar_evento(saida)
        return saida

    def tentar_proxima_onda(self):
        if self.modo != "coop":
            return []
        if not self.vivos_jogadores():
            return []
        if any(getattr(jogador, "tipo", "") == "chefe" and jogador.hp > 0 for jogador in self.jogadores):
            return []
        if self.onda >= self.ONDAS_MAX:
            return []
        from monstro import Monstro

        self.onda += 1
        chefe = Monstro.gerar_chefe(self.onda)
        self.jogadores.append(chefe)
        return [evento("onda", de=chefe.nome, onda=self.onda)]

    def registrar_evento(self, ev):
        if not ev:
            return []
        lista = ev if isinstance(ev, list) else [ev]
        self.eventos.extend(lista)
        self.eventos = self.eventos[-80:]
        return lista

    def verificar_mortos(self):
        novos = []
        for jogador in self.jogadores:
            if jogador.hp <= 0 and jogador not in self.mortos:
                self.mortos.append(jogador)
                novos.append(evento("morte", de=jogador.nome))
        self.registrar_evento(novos)
        return novos

    def lista_mortos(self):
        return {
            "vivos": [jog.nome for jog in self.vivos()],
            "mortos": [morto.nome for morto in self.mortos],
        }

    @classmethod
    def ganhar_moeda(cls, jog: Jogador, rodada, silencioso=False):
        moedamax = int(4 + rodada / 4)
        moeda = randint(1, moedamax)
        chance = randint(1, 3)
        if chance == 1:
            jog.moedas += moeda
            jog.ganhar_experiencia(10)
            return evento("moedas", de=nome(jog), moedas=moeda)
        return None

    def iniciar_rodada(self):
        for jogador in self.vivos():
            if hasattr(jogador, "inicio_rodada"):
                jogador.inicio_rodada()

    def gerar_evento_monstro(self, rodada):
        if rodada <= 2:
            chance = 1
        elif rodada <= 5:
            chance = 2
        elif rodada <= 10:
            chance = 3
        else:
            chance = 4
        chance += max(0, (rodada - 1) // 10)
        if randint(1, 100) <= chance:
            from monstro import Monstro

            return Monstro.gerar_monstro(max(1, (rodada // 2) + 1))
        return None

    def gerar_evento_aleatorio(self, rodada, jogador=None):
        return gerar_evento(rodada, jogador)

    def resolver_evento_aleatorio(self, jogador, ev, rodada=1):
        if not ev:
            return None
        if ev.get("tipo") == "monstro":
            return self.resolver_evento_monstro(jogador, ev["monstro"])
        resultado = resolver_evento(jogador, ev, rodada)
        self.registrar_evento(resultado)
        return resultado

    def resolver_evento_monstro(self, jogador, monstro):
        eventos = [evento("monstro", de=nome(jogador), nome=monstro.nome, para=jogador.nome)]
        while monstro.hp > 0 and jogador.hp > 0:
            resultado = resolver_ataque(jogador, monstro)
            eventos.extend(resultado.get("eventos") or [resultado])
            if not resultado["acertou"] and resultado.get("motivo") != "erro":
                break
            if monstro.hp <= 0:
                break
            contra = monstro.atacar(jogador)
            if isinstance(contra, dict):
                eventos.extend(contra.get("eventos") or [contra])
            if jogador.hp <= 0:
                break

        if monstro.hp <= 0:
            jogador.moedas += monstro.recompensa
            jogador.ganhar_experiencia(monstro.xp)
            eventos.append(evento("morte", de=monstro.nome))
            self.registrar_evento(eventos)
            return True
        eventos.append(evento("morte", de=jogador.nome))
        self.registrar_evento(eventos)
        return False

    def usar_magia(self, jog, nome_magia, alvo):
        return jog.usar_magia(nome_magia, alvo)

    def resultado_fim(self):
        vivos = self.vivos()
        if self.modo == "coop":
            if not self.vivos_jogadores():
                return evento("fim", vencedor=None, acabou=True)
            monstros = [j for j in vivos if j not in self.vivos_jogadores()]
            if not monstros:
                nomes = ", ".join(j.nome for j in self.vivos_jogadores())
                return evento("fim", vencedor=nomes or "grupo", acabou=True)
            return evento("fim", vencedor=None, acabou=False)
        if len(vivos) == 0:
            return evento("fim", vencedor=None, acabou=True)
        if len(vivos) == 1:
            return evento("fim", vencedor=vivos[0].nome, acabou=True)
        return evento("fim", vencedor=None, acabou=False)

    def fim_partida(self):
        if self.modo == "coop":
            self.tentar_proxima_onda()
        resultado = self.resultado_fim()
        if resultado.get("acabou"):
            self.registrar_evento(resultado)
        return bool(resultado.get("acabou"))

    def log_textos(self):
        return textos(self.eventos)
