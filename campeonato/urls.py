from django.urls import path, include
from . import views

app_name = 'campeonato'

urlpatterns = [
    # Páginas públicas
    path('', views.index, name='index'),
    path('buscar/', views.buscar_campeonatos, name='buscar_campeonatos'),
    path('c/<str:codigo_publico>/', views.campeonato_publico, name='campeonato_publico'),
    
    # Sistema administrativo (requer login)
    path('painel/', include([
        path('', views.dashboard, name='dashboard'),
        path('login/', views.admin_login, name='painel_login'),
        path('registro/', views.painel_registro, name='painel_registro'),
        path('logout/', views.admin_logout, name='admin_logout'),
        path('escolher-tenant/', views.escolher_tenant, name='escolher_tenant'),
        
        # Perfil e configurações do usuário
        path('perfil/', views.perfil, name='perfil'),
        path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
        path('configuracoes/', views.configuracoes, name='configuracoes'),
        
        # API endpoints
        path('api/planos-data/', views.api_planos_data, name='api_planos_data'),
        
        # Campeonatos
        path('campeonatos/', views.campeonatos_list, name='campeonatos_list'),
        path('campeonatos/criar/', views.campeonato_create, name='campeonato_create'),
        path('campeonatos/<int:pk>/', views.campeonato_detail, name='campeonato_detail'),
        path('campeonatos/<int:pk>/editar/', views.campeonato_update, name='campeonato_update'),
        path('campeonatos/<int:pk>/deletar/', views.campeonato_delete, name='campeonato_delete'),
        path('campeonatos/<int:pk>/gerenciar/', views.campeonato_gerenciar, name='campeonato_gerenciar'),
        
        # Gerenciamento de vínculos no campeonato
        path('campeonatos/<int:campeonato_pk>/times/<int:time_campeonato_pk>/vincular-jogador/', 
             views.vincular_jogador_time, name='vincular_jogador_time'),
        path('campeonatos/<int:campeonato_pk>/jogadores/<int:vinculo_pk>/desvincular/', 
             views.desvincular_jogador_time, name='desvincular_jogador_time'),
        path('campeonatos/<int:campeonato_pk>/times/<int:time_campeonato_pk>/desvincular/', 
             views.desvincular_time_campeonato, name='desvincular_time_campeonato'),
        path('campeonatos/<int:campeonato_pk>/times/<int:time_campeonato_pk>/editar/',
             views.editar_time_campeonato, name='editar_time_campeonato'),
        
        # URLs específicas para o gerenciamento
        path('campeonatos/<int:campeonato_pk>/times/<int:time_campeonato_pk>/jogadores/',
             views.jogadores_time, name='jogadores_time'),
        path('campeonatos/<int:campeonato_pk>/vincular-time/',
             views.vincular_time_view, name='vincular_time'),
        path('campeonatos/<int:campeonato_pk>/times/<int:time_campeonato_pk>/remover/',
             views.desvincular_time, name='desvincular_time'),
        
        # Profissionais no campeonato
        path('campeonatos/<int:campeonato_pk>/profissionais/vincular/', 
             views.vincular_profissional_campeonato, name='vincular_profissional_campeonato'),
        path('campeonatos/<int:campeonato_pk>/profissionais/<int:vinculo_pk>/desvincular/', 
             views.desvincular_profissional_campeonato, name='desvincular_profissional_campeonato'),
        path('campeonatos/<int:campeonato_pk>/profissionais/editar/', 
             views.editar_profissional_campeonato, name='editar_profissional_campeonato'),
        
        # URLs específicas para profissionais  
        path('campeonatos/<int:campeonato_pk>/vincular-profissional/',
             views.vincular_profissional_view, name='vincular_profissional'),
        path('campeonatos/<int:campeonato_pk>/profissionais/<int:profissional_campeonato_pk>/remover/',
             views.desvincular_profissional, name='desvincular_profissional'),
        
        # Times
        path('times/', views.times_list, name='times_list'),
        path('times/criar/', views.time_create, name='time_create'),
        path('times/<int:pk>/', views.time_detail, name='time_detail'),
        path('times/<int:pk>/editar/', views.time_update, name='time_update'),
        path('times/<int:pk>/deletar/', views.time_delete, name='time_delete'),
        
        # Alias para edição com redirecionamento para campeonato
        path('times/<int:pk>/edit/', views.time_edit, name='time_edit'),
        
        # Jogadores
        path('jogadores/', views.jogadores_list, name='jogadores_list'),
        path('jogadores/criar/', views.jogador_create, name='jogador_create'),
        path('jogadores/<int:pk>/', views.jogador_detail, name='jogador_detail'),
        path('jogadores/<int:pk>/editar/', views.jogador_update, name='jogador_update'),
        path('jogadores/<int:pk>/deletar/', views.jogador_delete, name='jogador_delete'),
        
        # Profissionais
        path('profissionais/', views.profissionais_list, name='profissionais_list'),
        path('profissionais/criar/', views.profissional_create, name='profissional_create'),
        path('profissionais/<int:pk>/', views.profissional_detail, name='profissional_detail'),
        path('profissionais/<int:pk>/editar/', views.profissional_update, name='profissional_update'),
        path('profissionais/<int:pk>/deletar/', views.profissional_delete, name='profissional_delete'),
        
        # Alias para edição com redirecionamento para campeonato
        path('profissionais/<int:pk>/edit/', views.profissional_edit, name='profissional_edit'),
        
        # Rodadas e Partidas
        path('campeonatos/<int:campeonato_pk>/gerar-rodadas/', 
             views.gerar_rodadas_campeonato, name='gerar_rodadas'),
        path('rodadas/<int:rodada_pk>/editar/', 
             views.editar_rodada, name='editar_rodada'),
        path('partidas/<int:partida_pk>/gerenciar/', 
             views.gerenciar_partida, name='gerenciar_partida'),
        
        # APIs para modais de edição
        path('api/rodadas/<int:rodada_pk>/', 
             views.rodada_detail_api, name='rodada_detail'),
        path('api/rodadas/<int:rodada_pk>/atualizar/', 
             views.rodada_update_api, name='rodada_update'),
        path('api/partidas/<int:partida_pk>/', 
             views.partida_detail_api, name='partida_detail'),
        path('api/partidas/<int:partida_pk>/atualizar/', 
             views.partida_update_api, name='partida_update'),
        
        # AJAX/API endpoints para funcionalidades dinâmicas (comentado temporariamente)
        # path('api/stats/', views.dashboard_stats, name='dashboard_stats'),
        # path('api/campeonatos/search/', views.campeonatos_search, name='campeonatos_search'),
        path('campeonatos/<int:campeonato_pk>/noticias-midia/', views.noticias_midia, name='noticias_midia'),
    ])),
]
