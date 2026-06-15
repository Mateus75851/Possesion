from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Campeonato, Clube, Participacao
from .serializers import CampeonatoSerializer, ClubeSerializer, ParticipacaoSerializer, ClassificacaoSerializer


class CampeonatoViewSet(viewsets.ModelViewSet):
    queryset = Campeonato.objects.all()
    serializer_class = CampeonatoSerializer

    @action(detail=True, methods=['get'])
    def classificacao(self, request, pk=None):
        campeonato = self.get_object()
        queryset_classificacao = campeonato.participacoes.annotate(
            saldo_de_gols=F('gols_feitos')-F('gols_sofridos')
        ).order_by('-pontos', '-vitorias', '-saldo_de_gols', '-gols_feitos')
        dicionario_classificacao = ClassificacaoSerializer(queryset_classificacao, many=True).data 

        return Response(dicionario_classificacao)





class ClubeViewSet(viewsets.ModelViewSet):
    queryset = Clube.objects.all()
    serializer_class = ClubeSerializer

class ParticipacaoViewSet(viewsets.ModelViewSet):
    queryset = Participacao.objects.all()
    serializer_class = ParticipacaoSerializer


