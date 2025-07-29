from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.urls import reverse
from .models import *
from adminpanel.models import Tenant
import secrets
import string


def index(request):
    """Página pública inicial do sistema"""
    # Buscar campeonatos públicos (por exemplo, os últimos 10)
    campeonatos_publicos = Campeonato.objects.select_related('tenant').order_by('-data_inicio')[:10]
    
    context = {
        'campeonatos': campeonatos_publicos,
        'title': 'KAMPEONATO - Sistema de Gerenciamento de Campeonatos'
    }
    return render(request, 'public/index.html', context)


def buscar_campeonatos(request):
    """Busca pública de campeonatos"""
    query = request.GET.get('q', '')
    campeonatos = Campeonato.objects.select_related('tenant')
    
    if query:
        campeonatos = campeonatos.filter(
            Q(nome__icontains=query) |
            Q(edicao__icontains=query) |
            Q(organizador__icontains=query)
        )
    
    campeonatos = campeonatos.order_by('-data_inicio')
    
    # Paginação
    paginator = Paginator(campeonatos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'title': 'Buscar Campeonatos'
    }
    return render(request, 'public/buscar_campeonatos.html', context)


def campeonato_publico(request, slug):
    """Página pública de um campeonato específico"""
    try:
        campeonato = get_object_or_404(Campeonato, pk=slug)
    except:
        # Se não for um ID numérico, buscar por slug customizado
        # Por enquanto vamos assumir que o slug é o ID
        raise Http404("Campeonato não encontrado")
    
    # Buscar dados do campeonato
    times = TimeCampeonato.objects.filter(campeonato=campeonato).select_related('time')
    rodadas = Rodada.objects.filter(campeonato=campeonato).order_by('numero')
    
    # Estatísticas básicas
    total_partidas = Partida.objects.filter(rodada__campeonato=campeonato).count()
    partidas_finalizadas = Partida.objects.filter(
        rodada__campeonato=campeonato, 
        status='finalizada'
    ).count()
    
    # Artilheiros (top 10)
    artilheiros = (
        Gol.objects.filter(partida__rodada__campeonato=campeonato)
        .values('jogador__jogador__nome', 'time__time__nome')
        .annotate(gols=Count('id'))
        .order_by('-gols')[:10]
    )
    
    context = {
        'campeonato': campeonato,
        'times': times,
        'rodadas': rodadas,
        'total_partidas': total_partidas,
        'partidas_finalizadas': partidas_finalizadas,
        'artilheiros': artilheiros,
        'title': f'{campeonato.nome} - {campeonato.edicao}'
    }
    return render(request, 'public/campeonato_detalhes.html', context)


# ========== ÁREA ADMINISTRATIVA ==========

def login_view(request):
    """Login do sistema"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        cpf = request.POST.get('cpf')
        password = request.POST.get('password')
        
        user = authenticate(request, username=cpf, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'CPF ou senha inválidos.')
    
    return render(request, 'auth/login.html', {'title': 'Login'})


def logout_view(request):
    """Logout do sistema"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('index')


@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    # Buscar tenant do usuário
    try:
        tenant = Tenant.objects.get(usuario=request.user)
    except Tenant.DoesNotExist:
        messages.error(request, 'Usuário não possui um tenant associado.')
        return redirect('index')
    
    # Estatísticas do tenant
    total_campeonatos = Campeonato.objects.filter(tenant=tenant).count()
    total_times = Time.objects.filter(tenant=tenant).count()
    total_jogadores = Jogador.objects.filter(tenant=tenant).count()
    total_profissionais = Profissional.objects.filter(tenant=tenant).count()
    
    # Campeonatos recentes
    campeonatos_recentes = Campeonato.objects.filter(tenant=tenant).order_by('-data_inicio')[:5]
    
    context = {
        'tenant': tenant,
        'total_campeonatos': total_campeonatos,
        'total_times': total_times,
        'total_jogadores': total_jogadores,
        'total_profissionais': total_profissionais,
        'campeonatos_recentes': campeonatos_recentes,
        'title': 'Dashboard'
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def campeonatos_list(request):
    """Lista de campeonatos do usuário"""
    tenant = get_object_or_404(Tenant, usuario=request.user)
    campeonatos = Campeonato.objects.filter(tenant=tenant).order_by('-data_inicio')
    
    # Paginação
    paginator = Paginator(campeonatos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Meus Campeonatos'
    }
    return render(request, 'admin/campeonatos/list.html', context)


@login_required
def campeonato_create(request):
    """Criar novo campeonato"""
    tenant = get_object_or_404(Tenant, usuario=request.user)
    
    if request.method == 'POST':
        try:
            campeonato = Campeonato.objects.create(
                tenant=tenant,
                nome=request.POST.get('nome'),
                edicao=request.POST.get('edicao'),
                organizador=request.POST.get('organizador'),
                data_inicio=request.POST.get('data_inicio'),
                data_fim=request.POST.get('data_fim') if request.POST.get('data_fim') else None,
                tipo_formato=request.POST.get('tipo_formato'),
                ida_volta=request.POST.get('ida_volta') == 'on',
                num_turnos=int(request.POST.get('num_turnos', 1)),
                num_grupos=int(request.POST.get('num_grupos', 0)),
                num_divisoes=int(request.POST.get('num_divisoes', 0)),
                num_classificados=int(request.POST.get('num_classificados', 0)),
                observacoes_formato=request.POST.get('observacoes_formato'),
                disputa_terceiro=request.POST.get('disputa_terceiro') == 'on',
                confrontos_mesmo_grupo=request.POST.get('confrontos_mesmo_grupo') == 'on'
            )
            messages.success(request, 'Campeonato criado com sucesso!')
            return redirect('campeonato_detail', pk=campeonato.pk)
        except Exception as e:
            messages.error(request, f'Erro ao criar campeonato: {str(e)}')
    
    context = {
        'title': 'Novo Campeonato',
        'formato_choices': Campeonato.FORMATO_CHOICES
    }
    return render(request, 'admin/campeonatos/create.html', context)


@login_required
def campeonato_detail(request, pk):
    """Detalhes de um campeonato"""
    tenant = get_object_or_404(Tenant, usuario=request.user)
    campeonato = get_object_or_404(Campeonato, pk=pk, tenant=tenant)
    
    # Estatísticas do campeonato
    total_times = TimeCampeonato.objects.filter(campeonato=campeonato).count()
    total_rodadas = Rodada.objects.filter(campeonato=campeonato).count()
    total_partidas = Partida.objects.filter(rodada__campeonato=campeonato).count()
    
    context = {
        'campeonato': campeonato,
        'total_times': total_times,
        'total_rodadas': total_rodadas,
        'total_partidas': total_partidas,
        'title': f'{campeonato.nome} - {campeonato.edicao}'
    }
    return render(request, 'admin/campeonatos/detail.html', context)


def gerar_slug_campeonato():
    """Gera um slug único para o campeonato"""
    chars = string.ascii_lowercase + string.digits
    while True:
        slug = ''.join(secrets.choice(chars) for _ in range(8))
        if not Campeonato.objects.filter(slug=slug).exists():
            return slug
