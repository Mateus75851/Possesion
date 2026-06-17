from random import choice
from django.db import transaction
from .models import Partida


def funcao_gerar_tabela(campeonato):
    with transaction.atomic():
        participacoes = list(campeonato.participacoes.all())

        numero_equipes = len(participacoes)

        if numero_equipes % 2 != 0:
            raise ValueError('O campeonato precisa ter um número par de times')
        
        rodadas = []

        partidas_casa = {p.id: 0 for p in participacoes}

        # primeiro turno
        for rodada in range(numero_equipes-1):
            jogos_rodada = []

            index_ultimo = numero_equipes-1

            total_jogos = numero_equipes//2

            # organizando mentalmente os times em fileira, vamos iniciar pegando os das pontas e aí ir entrando. Na primeira execução, participacoes[index_a] será o primeiro da fileira, enquanto participacoes[index_b] será o último. ao longo que a equipe_a for ficando mais à direita, automaticamente a equipe_b vai ficando mais à esquerda. Como esquema visual, pense na estrutura da regra para fazer a soma da PA.
            for i in range(total_jogos): 
                index_a = i
                index_b = index_ultimo-i

                equipe_a = participacoes[index_a]
                equipe_b = participacoes[index_b]

                if partidas_casa[equipe_a.id] < partidas_casa[equipe_b.id]:
                    jogos_rodada.append((equipe_a, equipe_b))
                    partidas_casa[equipe_a.id] += 1
                elif partidas_casa[equipe_a.id] > partidas_casa[equipe_b.id]:
                    jogos_rodada.append((equipe_b, equipe_a))
                    partidas_casa[equipe_b.id] += 1
                else:
                    # se ambos tem a mesma quantia de jogos em casa, podemos sortear qual tupla vamos usar
                    escolha = choice([(equipe_a, equipe_b), (equipe_b, equipe_a)])
                    jogos_rodada.append(escolha)

                    if escolha == (equipe_a, equipe_b):
                        partidas_casa[equipe_a.id] += 1
                    else:
                        partidas_casa[equipe_b.id] += 1

            
            # mantendo o time de index 0 fixo e rodando os outros
            participacoes.insert(1, participacoes.pop())
            rodadas.append(jogos_rodada)

        rodadas_segundo_turno = []

        # segundo turno
        for jogos_rodada in rodadas: # pego o conjunto de jogos, representado por tuplas, em cada rodada específica
            jogos_rodada_invertido = [] 

            for jogo in jogos_rodada:
                jogos_rodada_invertido.append((jogo[1], jogo[0])) # para cada tupla, eu coloco uma outra invertida na minha nova lista
            
            rodadas_segundo_turno.append(jogos_rodada_invertido) # e finalizo adicionando essa lista com as tuplas invertidas na minha lista de rodadas_segundo_turno
        
        rodadas += rodadas_segundo_turno # e adiciono as rodadas do segundo turno às rodadas que eu já tinha encontrado antes
        
        partidas_a_criar = [Partida(campeonato=campeonato, rodada=i+1, mandante=mandante, visitante=visitante) for i, rodada in enumerate(rodadas) for mandante, visitante in rodada] # pra cada i,rodada em enumerate (rodadas) E pra cada mandante e visitante nessa rodada, faça isso

        return Partida.objects.bulk_create(partidas_a_criar)