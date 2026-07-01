from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampeonatoViewSet, ClubeViewSet, PartidaViewSet, EstatisticaViewSet, AtletaViewSet, EscalacaoSlotViewSet, GolViewSet

router = DefaultRouter()

router.register('campeonatos', CampeonatoViewSet)
router.register('clubes', ClubeViewSet)
router.register('partidas', PartidaViewSet)
router.register('estatisticas', EstatisticaViewSet)
router.register('atletas', AtletaViewSet)
router.register('escalacoesslots', EscalacaoSlotViewSet)
router.register('gols', GolViewSet)

urlpatterns = [
    path('', include(router.urls))
]
