"""
URL configuration for kampeonato project - Template Mode

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Configuração padrão do Django Admin
admin.autodiscover()

urlpatterns = [
    # Django Admin - mantido para administração
    path('admin/', admin.site.urls),
    # API REST
    path('api/', include('campeonato.api_urls')),
    # Páginas públicas (home, busca, etc.)
    path('', include('campeonato.urls')),
    # Painel administrativo (inclui Mercado Pago)
    path('', include('adminpanel.urls')),
]

# Adicionar URLs para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
