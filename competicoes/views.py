from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Campeonato, Clube, Participacao, Partida, Estatistica, Atleta, Escalacao, EscalacaoSlot
from .serializers import CampeonatoSerializer, ClubeSerializer, ParticipacaoSerializer, PartidaSerializer, ClassificacaoSerializer, EstatisticaSerializer, AtletaSerializer, EscalacaoSerializer, EscalacaoSlotSerializer
from .services import funcao_gerar_tabela

class CampeonatoViewSet(viewsets.ModelViewSet):
    queryset = Campeonato.objects.all()
    serializer_class = CampeonatoSerializer

    @action(detail=True, methods=['get'])
    def classificacao(self, request, pk=None): # coloquei o None como padrão porque pode ter algum teste ou algo do tipo que eu queira usar sem passar o pk
        campeonato = self.get_object()
        queryset_classificacao = campeonato.participacoes.annotate(
            saldo_de_gols=F('gols_feitos')-F('gols_sofridos')
        ).order_by('-pontos', '-vitorias', '-saldo_de_gols', '-gols_feitos')
        dicionario_classificacao = ClassificacaoSerializer(queryset_classificacao, many=True).data 

        return Response(dicionario_classificacao)

    @action(detail=True, methods=['post', 'get'])
    def gerar_tabela(self, request, pk=None):
        campeonato = self.get_object()

        try:
            partidas = funcao_gerar_tabela(campeonato)
            
            return Response(
                {"message": f"Tabela gerada com sucesso! {len(partidas)} partidas criadas."},
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            # Se o erro for a falta de paridade ou campeonato já existente
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception:
            # Caso ocorra qualquer outro erro imprevisto
            return Response({"error": "Erro interno ao gerar a tabela."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ClubeViewSet(viewsets.ModelViewSet):
    queryset = Clube.objects.all()
    serializer_class = ClubeSerializer

class ParticipacaoViewSet(viewsets.ModelViewSet):
    queryset = Participacao.objects.all()
    serializer_class = ParticipacaoSerializer

class PartidaViewSet(viewsets.ModelViewSet):
    queryset = Partida.objects.all()
    serializer_class = PartidaSerializer

class EstatisticaViewSet(viewsets.ModelViewSet):
    queryset = Estatistica.objects.all()
    serializer_class = EstatisticaSerializer

class AtletaViewSet(viewsets.ModelViewSet):
    queryset = Atleta.objects.all()
    serializer_class = AtletaSerializer

class EscalacaoViewSet(viewsets.ModelViewSet):
    queryset = Escalacao.objects.all()
    serializer_class = EscalacaoSerializer

class EscalacaoSlotViewSet(viewsets.ModelViewSet):
    queryset = EscalacaoSlot.objects.all()
    serializer_class = EscalacaoSlotSerializer