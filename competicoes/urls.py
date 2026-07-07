from django.urls import include, path
from rest_framework_nested import routers

from competicoes.views import (
    AtletaViewSet,
    CampeonatoViewSet,
    ClubeViewSet,
    EscalacaoSlotViewSet,
    EstatisticaViewSet,
    GolViewSet,
    PartidaViewSet,
)

router = routers.SimpleRouter()

router.register("campeonatos", CampeonatoViewSet)

campeonatos_router = routers.NestedSimpleRouter(router, "campeonatos", lookup="campeonato")
campeonatos_router.register("partidas", PartidaViewSet, basename='campeonato-partidas')

router.register("clubes", ClubeViewSet)
router.register("estatisticas", EstatisticaViewSet)
router.register("atletas", AtletaViewSet)
router.register("escalacoesslots", EscalacaoSlotViewSet)
router.register("gols", GolViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(campeonatos_router.urls)),
    ]
