from rest_framework import viewsets
from .models import Campeonato, Clube, Participacao
from .serializers import CampeonatoSerializer, ClubeSerializer, ParticipacaoSerializer


class CampeonatoViewSet(viewsets.ModelViewSet):
    queryset = Campeonato.objects.all()
    serializer_class = CampeonatoSerializer

    '''@action(detail=True, methods=['get'])
    def classificacao(self, request, pk=None):
        campeonato = self.get_object()
        participacoes = campeonato.participacoes.all()'''





class ClubeViewSet(viewsets.ModelViewSet):
    queryset = Clube.objects.all()
    serializer_class = ClubeSerializer

class ParticipacaoViewSet(viewsets.ModelViewSet):
    queryset = Participacao.objects.all()
    serializer_class = ParticipacaoSerializer


