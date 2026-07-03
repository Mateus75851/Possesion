from django.db import transaction
from rest_framework import serializers
from .models import Campeonato, Clube, Participacao, Partida, Estatistica, Atleta, EscalacaoSlot, Gol

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
    
class EscalacaoSlotSerializer(serializers.ModelSerializer):
    clube = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EscalacaoSlot
        fields = '__all__'
    
    def get_clube(self, obj):
        clube = obj.atleta.clube.nome
        return clube

    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['atleta'] = instance.atleta.nome
        return representacao

class PartidaSerializer(serializers.ModelSerializer):
    estatisticas_mandante = EstatisticaSerializer()
    estatisticas_visitante = EstatisticaSerializer()

    escalacao_mandante = EscalacaoSlotSerializer(many=True, write_only=True)
    escalacao_visitante = EscalacaoSlotSerializer(many=True, write_only=True)


    class Meta:
        model = Partida
        fields = '__all__'
    
    def validate(self, data):
        # extração dos dados
        instance = self.instance

        rodada = data.get('rodada', instance.rodada if instance else None)
        status = data.get('status', instance.status if instance else None)
        estatisticas_mandante = data.get('estatisticas_mandante', instance.estatisticas_mandante if instance else None)
        estatisticas_visitante = data.get('estatisticas_visitante', instance.estatisticas_visitante if instance else None)
        mandante = data.get('mandante', instance.mandante if instance else None)
        visitante = data.get('visitante', instance.visitante if instance else None)
        escalacao_mandante = data.get('escalacao_mandante', [{'posicao_assumida': slot.posicao_assumida, 'partida': slot.partida, 'atleta': slot.atleta} for slot in instance.escalacao_slots.filter(atleta__clube=mandante.clube)] if instance else [])
        escalacao_visitante = data.get('escalacao_visitante', [{'posicao_assumida': slot.posicao_assumida, 'partida': slot.partida, 'atleta': slot.atleta} for slot in instance.escalacao_slots.filter(atleta__clube=visitante.clube)] if instance else [])

        # Verificação de dados necessários

        if (estatisticas_mandante and not estatisticas_visitante):
            raise serializers.ValidationError({'estatisticas_mandante': 'Não se pode ter as estatísticas do mandante sem as do visitante'})
        elif (estatisticas_visitante and not estatisticas_mandante):
            raise serializers.ValidationError({'estatisticas_visitante': 'Não se pode ter as estatísticas do visitante sem as do mandante'})

        # validações lógicas que não recorram ao banco

        if mandante == visitante:
            raise serializers.ValidationError({'mandante': 'Um clube não pode jogar contra ele mesmo'})

        if status != 'F' and estatisticas_mandante:
            raise serializers.ValidationError({'status': 'Não se pode ter uma partida não finalizada já com as estatisticas'})

        if estatisticas_mandante:
            porcentagem_posse_de_bola_mandante = estatisticas_mandante.get('porcentagem_posse_de_bola') if type(estatisticas_mandante) == dict else estatisticas_mandante.porcentagem_posse_de_bola
            porcentagem_posse_de_bola_visitante = estatisticas_visitante.get('porcentagem_posse_de_bola') if type(estatisticas_visitante) == dict else estatisticas_visitante.porcentagem_posse_de_bola

            if porcentagem_posse_de_bola_mandante + porcentagem_posse_de_bola_visitante != 100:
                raise serializers.ValidationError({'estatisticas_mandante': 'As porcentagens de posse de bola do mandante e do visitante precisam somar 100'})

        if escalacao_mandante:
            atletas_invalidos_mandante = [escalacao_slot['atleta'].nome for escalacao_slot in escalacao_mandante if escalacao_slot['atleta'].clube != mandante.clube]

            if atletas_invalidos_mandante:
                raise serializers.ValidationError({'escalacao_mandante': f'Os seguintes atletas não pertencem ao clube mandante: {atletas_invalidos_mandante}'})
            
        if escalacao_visitante:
            atletas_invalidos_visitante = [escalacao_slot['atleta'].nome for escalacao_slot in escalacao_visitante if escalacao_slot['atleta'].clube != visitante.clube]

            if atletas_invalidos_visitante:
                raise serializers.ValidationError({'escalacao_visitante': f'Os seguintes atletas não pertencem ao clube visitante: {atletas_invalidos_visitante}'})

        # validações lógicas que recorram ao banco

        if status == 'F':
            # vai pegando rodada a rodada ANTES da rodada da partida, com o intuito de confirmar se não ficou nenhum jogo pendente no caminho. Dessa forma, o cliente só vai poder finalizar algum jogo na rodada 8 se todos os jogos da rodada 1 a 7 tiverem sido finalizados(ou adiados), por exemplo, impedindo o cliente de pular rodadas.
            for rodada_anterior in range(1, rodada):
                partidas = Partida.objects.filter(rodada=rodada_anterior)
                for partida in partidas:
                    if partida.status == 'P':
                        raise serializers.ValidationError({'rodada': f'A partida {partida.__str__()} ainda está pendente'})

        return data


    def update(self, instance, validated_data):
        estatisticas_mandante_vieram = bool(validated_data.get('estatisticas_mandante'))
        estatisticas_visitante_vieram = bool(validated_data.get('estatisticas_visitante'))

        # extração dos dados
        estatisticas_mandante = validated_data.pop('estatisticas_mandante', instance.estatisticas_mandante)
        estatisticas_visitante = validated_data.pop('estatisticas_visitante', instance.estatisticas_visitante)
        estatisticas_mandante_antigas = instance.estatisticas_mandante
        estatisticas_visitante_antigas = instance.estatisticas_visitante
        mandante = validated_data.get('mandante', instance.mandante)
        visitante = validated_data.get('visitante', instance.visitante)



        partida_atualizada = super().update(instance, validated_data)

        if estatisticas_mandante_vieram or estatisticas_visitante_vieram:
            with transaction.atomic():

                estatisticas_mandante = estatisticas_mandante if type(estatisticas_mandante) == dict else EstatisticaSerializer(estatisticas_mandante).data
                estatisticas_visitante = estatisticas_visitante if type(estatisticas_visitante) == dict else EstatisticaSerializer(estatisticas_visitante).data

                # mexe nas instâncias de ESTATISTICA
                estatisticas_mandante, _ = Estatistica.objects.update_or_create(id=estatisticas_mandante_antigas.id if estatisticas_mandante_antigas else None, defaults=estatisticas_mandante)

                estatisticas_visitante, _ = Estatistica.objects.update_or_create(id=estatisticas_visitante_antigas.id if estatisticas_visitante_antigas else None, defaults=estatisticas_visitante)

                # muda os campos estatisticas_mandante e estatisticas_visitante da PARTIDA
                partida_atualizada.estatisticas_mandante = estatisticas_mandante
                partida_atualizada.estatisticas_visitante = estatisticas_visitante

                partida_atualizada.save()

                # recalcula as participações
                mandante.recalcular_totais()
                visitante.recalcular_totais()

        return partida_atualizada
    
    def to_representation(self, instance):
        representacao = super().to_representation(instance) # retorna um dicionário de primitivos
        representacao['campeonato'] = instance.campeonato.__str__()
        representacao['mandante'] = instance.mandante.clube.nome
        representacao['visitante'] = instance.visitante.clube.nome

        escalacao_mandante_queryset = instance.escalacao_slots.filter(atleta__clube=instance.mandante.clube)
        escalacao_visitante_queryset = instance.escalacao_slots.filter(atleta__clube=instance.visitante.clube) 

        escalacao_mandante_lista_dicionarios = EscalacaoSlotSerializer(escalacao_mandante_queryset, many=True).data
        escalacao_visitante_lista_dicionarios = EscalacaoSlotSerializer(escalacao_visitante_queryset, many=True).data

        representacao['escalacao_mandante'] = escalacao_mandante_lista_dicionarios
        representacao['escalacao_visitante'] = escalacao_visitante_lista_dicionarios


        return representacao
    
class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = '__all__'

class GolSerializer(serializers.ModelSerializer):
    clube = serializers.SerializerMethodField()
    minuto = serializers.IntegerField(min_value=1, max_value=115)

    class Meta:
        model = Gol
        fields = '__all__'
    
    def get_clube(self, obj):
        clube = obj.atleta.clube
        return clube

    def validate(self, data):
        if self.instance:
            partida = data.get('partida', self.instance.partida)
            atleta = data.get('atleta', self.instance.atleta)

        else:
            partida = data.get('partida')
            atleta = data.get('atleta')
        
        if atleta.clube != partida.mandante.clube and atleta.clube != partida.visitante.clube:
            raise serializers.ValidationError({'atleta': 'O clube a qual esse atleta é relacionado não participa dessa partida'})

        return data

    def to_representation(self, instance):
        representacao = super().to_representation(instance)
        representacao['clube'] = instance.atleta.clube.nome
        representacao['partida'] = instance.partida.__str__()
        representacao['atleta'] = instance.atleta.nome

        return representacao

class CadastroClubesSerializer(serializers.Serializer):
    clubes = serializers.PrimaryKeyRelatedField(queryset=Clube.objects.all(), many=True)

    def validate(self, data):
        quantidade_clubes_recebida = len(data.get('clubes'))
        quantidade_clubes_necessaria = self.context['campeonato'].quantidade_equipes

        if quantidade_clubes_recebida != quantidade_clubes_necessaria:
            raise serializers.ValidationError({'clubes': f'{quantidade_clubes_necessaria} clubes são necessários, mas {quantidade_clubes_recebida} foram recebidos'})
        return data

class ClassificacaoSerializer(serializers.ModelSerializer):
    clube = ClubeSerializer()
    pontos = serializers.IntegerField()
    saldo_de_gols = serializers.IntegerField()

    class Meta:
        model = Participacao
        fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
        read_only_fields = ['clube', 'pontos', 'vitorias', 'empates', 'derrotas', 'gols_feitos', 'gols_sofridos', 'saldo_de_gols']
