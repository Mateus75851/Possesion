from django.db import transaction
from rest_framework import serializers
from .models import Campeonato, Clube, Participacao, Partida, Estatistica, Atleta, Escalacao , EscalacaoSlot, Gol

class CampeonatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeonato
        fields = '__all__'

class ClubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clube
        fields = '__all__'

class ParticipacaoSerializer(serializers.ModelSerializer):
    pontos = serializers.SerializerMethodField()
    partidas = serializers.SerializerMethodField()
    saldo_de_gols = serializers.SerializerMethodField()

    class Meta:
        model = Participacao
        fields = ['id', 'campeonato', 'clube', 'pontos', 'partidas', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols', 'cartoes_amarelos', 'cartoes_vermelhos']
    
    def get_pontos(self, obj):
        vitorias = obj.vitorias
        empates = obj.empates

        pontos_de_vitorias = vitorias*3
        pontos_de_empate = empates

        pontos = pontos_de_vitorias + pontos_de_empate

        return pontos
    
    def get_partidas(self, obj):
        vitorias = obj.vitorias
        empates = obj.empates
        derrotas = obj.derrotas

        partidas = vitorias + empates + derrotas
        
        return partidas
    
    def get_saldo_de_gols(self, obj):
        gols_feitos = obj.gols_feitos
        gols_sofridos = obj.gols_sofridos

        saldo_de_gols = gols_feitos - gols_sofridos

        return saldo_de_gols
    
    def validate(self, data):
        if self.instance:
            vitorias = data.get('vitorias', self.instance.vitorias)
            gols_feitos = data.get('gols_feitos', self.instance.gols_feitos)
        else:
            vitorias = data.get('vitorias')
            gols_feitos = data.get('gols_feitos')

        if vitorias > gols_feitos:
            raise serializers.ValidationError({'vitorias': 'É matematicamente impossível se ter mais vitórias do que gols feitos'})

        return data
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['campeonato'] = instance.campeonato.__str__()
        representacao['clube'] = instance.clube.nome
        
        return representacao

class PartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = '__all__'
        extra_kwargs = {
            'estatisticas_mandante': {'write_only': True},
            'estatisticas_visitante': {'write_only': True},
            'escalacao_mandante': {'write_only': True},
            'escalacao_visitante': {'write_only': True},
        }
    
    def validate(self, data):
        if self.instance:
            rodada = data.get('rodada', self.instance.rodada)
            status = data.get('status', self.instance.status)
            estatisticas_mandante = data.get('estatisticas_mandante', self.instance.estatisticas_mandante)
            estatisticas_visitante = data.get('estatisticas_visitante', self.instance.estatisticas_visitante)
            mandante = data.get('mandante', self.instance.mandante)
            visitante = data.get('visitante', self.instance.visitante)
        else:
            rodada = data.get('rodada')
            status = data.get('status')
            estatisticas_mandante = data.get('estatisticas_mandante')
            estatisticas_visitante = data.get('estatisticas_visitante')
            mandante = data.get('mandante')
            visitante = data.get('visitante')

        if mandante == visitante:
            raise serializers.ValidationError({'mandante': 'Um clube não pode jogar contra ele mesmo'})

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

                elif estatisticas_mandante.gols == estatisticas_visitante.gols:
                    participacao_mandante.empates += 1
                    participacao_visitante.empates += 1

                else:
                    participacao_mandante.derrotas += 1
                    participacao_visitante.vitorias += 1

                
                participacao_mandante.save()
                participacao_visitante.save()
            

        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance) # retorna um dicionário de primitivos
        representacao['campeonato'] = instance.campeonato.__str__()
        representacao['mandante'] = instance.mandante.clube.nome
        representacao['visitante'] = instance.visitante.clube.nome
        representacao['escalacao_mandante'] = instance.escalacao_mandante.__str__()
        representacao['escalacao_visitante'] = instance.escalacao_visitante.__str__()
        return representacao

class EstatisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estatistica
        fields = '__all__'
    
    def validate(self, data):
        if self.instance:
            chutes = data.get('chutes', self.instance.chutes)
            chutes_a_gol = data.get('chutes_a_gol', self.instance.chutes_a_gol)
        else:
            chutes = data.get('chutes')
            chutes_a_gol = data.get('chutes_a_gol')

        if chutes_a_gol > chutes:
            raise serializers.ValidationError({'chutes_a_gol': 'Não pode haver mais chutes a gol do que chutes totais'})
        
        return data
    
class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = '__all__'

class EscalacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escalacao
        fields = '__all__'
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['clube'] = instance.clube.nome
        representacao['partida'] = instance.partida.__str__()
        return representacao
    
class EscalacaoSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscalacaoSlot
        fields = '__all__'
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['escalacao'] = instance.escalacao.__str__()
        representacao['atleta'] = instance.atleta.nome
        return representacao

class GolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gol
        fields = '__all__'
    
    def validate(self, data):
        # extração de dados
        if self.instance:
            minuto = data.get('minuto', self.instance.minuto)
            clube = data.get('clube', self.instance.clube)
            partida = data.get('partida', self.instance.partida)
            atleta = data.get('atleta', self.instance.atleta)

        else:
            minuto = data.get('minuto')
            clube = data.get('clube')
            partida = data.get('partida')
            atleta = data.get('atleta')

        if minuto > 115:
            raise serializers.ValidationError({'minuto': 'O gol não pode ter sido marcado depois do minuto 115'})
        
        if clube != partida.mandante.clube and clube != partida.visitante.clube:
            raise serializers.ValidationError({'clube': 'Esse clube não participa dessa partida'})
        
        if atleta.clube != clube:
            raise serializers.ValidationError({'atleta': 'Esse atleta não joga nesse clube'})


        # Regra de negócio

        return data

    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['clube'] = instance.clube.nome
        representacao['partida'] = instance.partida.__str__()
        representacao['atleta'] = instance.atleta.nome

        return representacao

class ClassificacaoSerializer(serializers.ModelSerializer):
    clube = ClubeSerializer()
    pontos = serializers.IntegerField()
    saldo_de_gols = serializers.IntegerField()

    class Meta:
        model = Participacao
        fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
        read_only_fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
