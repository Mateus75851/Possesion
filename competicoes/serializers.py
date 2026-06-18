from rest_framework import serializers
from .models import Campeonato, Clube, Participacao, Partida, Estatistica

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
        estatisticas_mandante = data.get('estatisticas_mandante') or getattr(self.instance, 'estatisticas_mandante', None)
        estatisticas_visitante = data.get('estatisticas_visitante') or getattr(self.instance, 'estatisticas_visitante', None)

        if (estatisticas_mandante and not estatisticas_visitante):
            raise serializers.ValidationError({'estatisticas_mandante': 'As estatísticas do mandante e do visitante precisam ser adicionadas juntas!'})
        elif (estatisticas_visitante and not estatisticas_mandante):
            raise serializers.ValidationError({'estatisticas_visitante': 'As estatísticas do mandante e do visitante precisam ser adicionadas juntas!'})
        
        return data


    def update(self, instance, validated_data):
        estatisticas_mandante = validated_data.get('estatisticas_mandante') or instance.estatisticas_mandante
        estatisticas_visitante = validated_data.get('estatisticas_visitante') or instance.estatisticas_visitante

        if estatisticas_mandante: # se temos as estatisticas do mandante(lembrando que, se tem do mandante, tem do visitante)
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

class ClassificacaoSerializer(serializers.ModelSerializer):
    clube = ClubeSerializer()
    saldo_de_gols = serializers.IntegerField()

    class Meta:
        model = Participacao
        fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
        read_only_fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']