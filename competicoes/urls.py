from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampeonatoViewSet, ClubeViewSet, ParticipacaoViewSet, PartidaViewSet, EstatisticaViewSet, AtletaViewSet

router = DefaultRouter()

router.register('campeonatos', CampeonatoViewSet)
router.register('clubes', ClubeViewSet)
router.register('participacoes', ParticipacaoViewSet)
router.register('partidas', PartidaViewSet)
router.register('estatisticas', EstatisticaViewSet)
router.register('atletas', AtletaViewSet)

urlpatterns = [
    path('', include(router.urls))
]
