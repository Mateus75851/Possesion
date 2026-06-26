from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Campeonato, Clube, Participacao, Partida, Estatistica, Atleta, Escalacao , EscalacaoSlot, Gol
from .serializers import CampeonatoSerializer, ClubeSerializer, ParticipacaoSerializer, PartidaSerializer, ClassificacaoSerializer, EstatisticaSerializer, AtletaSerializer, EscalacaoSerializer, EscalacaoSlotSerializer, GolSerializer
from .services import funcao_gerar_tabela

class CampeonatoViewSet(viewsets.ModelViewSet):
    queryset = Campeonato.objects.all()
    serializer_class = CampeonatoSerializer

    @action(detail=True, methods=['get'])
    def classificacao(self, request, pk=None): # coloquei o None como padrão porque pode ter algum teste ou algo do tipo que eu queira usar sem passar o pk
        campeonato = self.get_object()
        queryset_classificacao = campeonato.participacoes.annotate(
            pontos=F('vitorias')*3 + F('empates'),
            saldo_de_gols=F('gols_feitos')-F('gols_sofridos'),
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



class PartidaViewSet(viewsets.ModelViewSet):
    queryset = Partida.objects.all()
    serializer_class = PartidaSerializer

    @action(detail=True, methods=['get'])
    def mostrar_estatisticas(self, request, pk=None):
        partida = self.get_object()
        nome_mandante = partida.mandante.clube.nome
        nome_visitante = partida.visitante.clube.nome

        estatisticas_mandante = EstatisticaSerializer(partida.estatisticas_mandante).data
        estatisticas_visitante = EstatisticaSerializer(partida.estatisticas_visitante).data

        return Response({
            nome_mandante: estatisticas_mandante,
            nome_visitante: estatisticas_visitante,
        })
    
    @action(detail=True, methods=['get'])
    def mostrar_escalacoes(self, request, pk=None):
        partida = self.get_object()
        nome_mandante = partida.mandante.clube.nome
        nome_visitante = partida.visitante.clube.nome

        queryset_escalacao_mandante = EscalacaoSlot.objects.filter(escalacao=partida.escalacao_mandante)
        queryset_escalacao_visitante = EscalacaoSlot.objects.filter(escalacao=partida.escalacao_visitante)

        lista_dicionarios_escalacao_mandante = EscalacaoSlotSerializer(queryset_escalacao_mandante, many=True).data
        lista_dicionarios_escalacao_visitante = EscalacaoSlotSerializer(queryset_escalacao_visitante, many=True).data



        return Response({
            nome_mandante: lista_dicionarios_escalacao_mandante,
            nome_visitante: lista_dicionarios_escalacao_visitante,
        })
    
    @action(detail=True, methods=['get'])
    def placar(self, request, pk=None):
        partida = self.get_object()

        clube_mandante = partida.mandante.clube
        clube_visitante = partida.visitante.clube

        nome_mandante = clube_mandante.nome
        nome_visitante = clube_visitante.nome

        queryset_gols_mandante = Gol.objects.filter(partida=partida, atleta__clube=clube_mandante)
        queryset_gols_visitante = Gol.objects.filter(partida=partida, atleta__clube=clube_visitante)

        lista_dicionarios_gols_mandante = GolSerializer(queryset_gols_mandante, many=True).data
        lista_dicionarios_gols_visitante = GolSerializer(queryset_gols_visitante, many=True).data

        quantidade_gols_mandante = partida.estatisticas_mandante.gols
        quantidade_gols_visitante = partida.estatisticas_visitante.gols

        return Response({
            nome_mandante: quantidade_gols_mandante,
            nome_visitante: quantidade_gols_visitante,
            'gols_mandante': lista_dicionarios_gols_mandante,
            'gols_visitante': lista_dicionarios_gols_visitante,
        })

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

class GolViewSet(viewsets.ModelViewSet):
    queryset = Gol.objects.all()
    serializer_class = GolSerializer