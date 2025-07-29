from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    TimeViewSet, JogadorViewSet, ProfissionalViewSet,
    CampeonatoViewSet, TimeCampeonatoViewSet, RodadaViewSet,
    PartidaViewSet, DashboardViewSet, AuthViewSet,
    GolViewSet, CartaoViewSet
)

# Criar o router e registrar as ViewSets
router = DefaultRouter()
router.register(r'times', TimeViewSet)
router.register(r'jogadores', JogadorViewSet)
router.register(r'profissionais', ProfissionalViewSet)
router.register(r'campeonatos', CampeonatoViewSet)
router.register(r'times-campeonato', TimeCampeonatoViewSet)
router.register(r'rodadas', RodadaViewSet)
router.register(r'partidas', PartidaViewSet)
router.register(r'gols', GolViewSet)
router.register(r'cartoes', CartaoViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'auth', AuthViewSet, basename='auth')

# Definir funções para views customizadas
from .api_views import TimeCampeonatoViewSet

# Criar URLs personalizadas para ações específicas
desvincular_jogador_view = TimeCampeonatoViewSet.as_view({
    'post': 'desvincular_jogador',
})

urlpatterns = [
    # URLs da API (sem prefixo adicional, pois já vem de /api/)
    path('', include(router.urls)),
    
    # URL customizada para desvincular jogador (rota alternativa)
    path('times-campeonato/<int:pk>/desvincular_jogador/', desvincular_jogador_view, name='desvincular-jogador'),
]
