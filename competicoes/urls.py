from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampeonatoViewSet, ClubeViewSet, ParticipacaoViewSet

router = DefaultRouter()

router.register('campeonatos', CampeonatoViewSet)
router.register('clubes', ClubeViewSet)
router.register('participacoes', ParticipacaoViewSet)

urlpatterns = [
    path('', include(router.urls))
]
