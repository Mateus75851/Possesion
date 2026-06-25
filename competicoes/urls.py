from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampeonatoViewSet, ClubeViewSet, ParticipacaoViewSet, PartidaViewSet, EstatisticaViewSet, AtletaViewSet, EscalacaoViewSet , EscalacaoSlotViewSet, GolViewSet

router = DefaultRouter()

router.register('campeonatos', CampeonatoViewSet)
router.register('clubes', ClubeViewSet)
router.register('participacoes', ParticipacaoViewSet)
router.register('partidas', PartidaViewSet)
router.register('estatisticas', EstatisticaViewSet)
router.register('atletas', AtletaViewSet)
router.register('escalacoes', EscalacaoViewSet)
router.register('escalacoesslots', EscalacaoSlotViewSet)
router.register('gols', GolViewSet)

urlpatterns = [
    path('', include(router.urls))
]
