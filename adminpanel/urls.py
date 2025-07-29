from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_mercadopago import checkout_mercadopago, mercadopago_webhook

# Estas URLs serão acessadas via /gestao/...
urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),  # Página inicial do painel
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard_detail'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),
    # Mercado Pago
    path('checkout/mercadopago/<str:plano_id>/<str:periodicidade>/', checkout_mercadopago, name='checkout_mercadopago'),
    path('mercadopago/webhook/', mercadopago_webhook, name='mercadopago_webhook'),
]
