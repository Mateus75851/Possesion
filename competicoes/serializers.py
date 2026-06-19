from django.db import transaction
from rest_framework import serializers
from .models import Campeonato, Clube, Participacao, Partida, Estatistica, Atleta, Escalacao, EscalacaoSlot

class CampeonatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeonato
        fields = '__all__'

class ClubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clube
        fields = '__all__'

class ParticipacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacao
        fields = '__all__'

class PartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = '__all__'
    
    def validate(self, data):
        rodada = data.get('rodada') or getattr(self.instance, 'rodada', None)
        status = data.get('status') or getattr(self.instance, 'status', None)
        estatisticas_mandante = data.get('estatisticas_mandante') or getattr(self.instance, 'estatisticas_mandante', None)
        estatisticas_visitante = data.get('estatisticas_visitante') or getattr(self.instance, 'estatisticas_visitante', None)

        if status == 'F':
            # vai pegando rodada a rodada ANTES da rodada da partida, com o intuito de confirmar se não ficou nenhum jogo pendente no caminho. Dessa forma, o cliente só vai poder finalizar algum jogo na rodada 8 se todos os jogos da rodada 1 a 7 tiverem sido finalizados(ou adiados), por exemplo, impedindo o cliente de pular rodadas.
            for rodada_anterior in range(1, rodada):
                partidas = Partida.objects.filter(rodada=rodada_anterior)
                for partida in partidas:
                    if partida.status == 'P':
                        raise serializers.ValidationError({'rodada': f'A partida {partida.__str__()} ainda está pendente'})

        if (estatisticas_mandante and not estatisticas_visitante):
            raise serializers.ValidationError({'estatisticas_mandante': 'As estatísticas do mandante e do visitante precisam ser adicionadas juntas!'})
        elif (estatisticas_visitante and not estatisticas_mandante):
            raise serializers.ValidationError({'estatisticas_visitante': 'As estatísticas do mandante e do visitante precisam ser adicionadas juntas!'})
        
        if status != 'F' and estatisticas_mandante:
            raise serializers.ValidationError({'status': 'Não se pode ter uma partida não finalizada já com as estatisticas'})
        
        if estatisticas_mandante:
            if estatisticas_mandante.porcentagem_posse_de_bola + estatisticas_visitante.porcentagem_posse_de_bola != 100:
                raise serializers.ValidationError({'estatisticas_mandante': 'As porcentagens de posse de bola do mandante e do visitante precisam somar 100'})
        
        return data


    def update(self, instance, validated_data):
        estatisticas_mandante = validated_data.get('estatisticas_mandante') or instance.estatisticas_mandante
        estatisticas_visitante = validated_data.get('estatisticas_visitante') or instance.estatisticas_visitante

        if estatisticas_mandante: # se temos as estatisticas do mandante(lembrando que, se tem do mandante, tem do visitante)
            with transaction.atomic():
                participacao_mandante = instance.mandante
                participacao_visitante = instance.visitante
                
                # contamos os gols que cada um fez e sofreu
                participacao_mandante.gols_feitos += estatisticas_mandante.gols
                participacao_mandante.gols_sofridos += estatisticas_visitante.gols

                participacao_visitante.gols_feitos += estatisticas_visitante.gols
                participacao_visitante.gols_sofridos += estatisticas_mandante.gols

                # contamos os cartoes amarelos e vermelhos que cada um levou
                participacao_mandante.cartoes_amarelos += estatisticas_mandante.cartoes_amarelos
                participacao_mandante.cartoes_vermelhos += estatisticas_mandante.cartoes_vermelhos

                participacao_visitante.cartoes_amarelos += estatisticas_visitante.cartoes_amarelos
                participacao_visitante.cartoes_vermelhos += estatisticas_visitante.cartoes_vermelhos

                # analisamos quem venceu ou se deu empate
                if estatisticas_mandante.gols > estatisticas_visitante.gols:
                    participacao_mandante.vitorias += 1
                    participacao_visitante.derrotas += 1

                    participacao_mandante.pontos += 3
                elif estatisticas_mandante.gols == estatisticas_visitante.gols:
                    participacao_mandante.empates += 1
                    participacao_visitante.empates += 1

                    participacao_mandante.pontos += 1
                    participacao_visitante.pontos += 1
                else:
                    participacao_mandante.derrotas += 1
                    participacao_visitante.vitorias += 1

                    participacao_visitante.pontos += 3
                
                participacao_mandante.save()
                participacao_visitante.save()
            

        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance) # retorna um dicionário de primitivos
        representacao['campeonato'] = instance.campeonato.__str__()
        representacao['mandante'] = instance.mandante.clube.nome
        representacao['visitante'] = instance.visitante.clube.nome
        return representacao

class EstatisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estatistica
        fields = '__all__'
    
    def validate(self, data):
        chutes = data.get('chutes') or getattr(self.instance, 'chutes', 0)
        chutes_a_gol = data.get('chutes_a_gol') or getattr(self.instance, 'chutes_a_gol', 0)

        if chutes_a_gol > chutes:
            raise serializers.ValidationError({'chutes_a_gol': 'Não pode haver mais chutes a gol do que chutes totais'})
        
        return data
    
class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = '__all__'

class EscalacaoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escalacao
        fields = '__all__'

class EscalacaoSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscalacaoSlot
        fields = '__all__'


class ClassificacaoSerializer(serializers.ModelSerializer):
    clube = ClubeSerializer()
    saldo_de_gols = serializers.IntegerField()

    class Meta:
        model = Participacao
        fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
        read_only_fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']