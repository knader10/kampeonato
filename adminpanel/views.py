from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from django.db import transaction

from .forms import LoginForm, RegistroForm, PerfilForm, AlterarSenhaForm
from .models import Tenant


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        form = LoginForm()
    return render(request, 'adminpanel/login.html', {'form': form})


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # Usar uma transação para garantir que o usuário e o tenant sejam criados juntos
            with transaction.atomic():
                user = form.save()
                email = form.cleaned_data.get('email')
                
                # Garante que o tenant seja criado antes do login
                tenant, created = Tenant.objects.get_or_create(
                    usuario=user,
                    defaults={
                        'nome': email,
                        'subdominio': f"{slugify(email.split('@')[0])}-{user.id}"
                    }
                )

            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegistroForm()
    return render(request, 'adminpanel/registro.html', {'form': form})


@login_required
def dashboard_view(request):
    from campeonato.models import Time, Jogador, Campeonato, Partida
    from django.utils import timezone
    from django.db.models import Q
    
    # Data e hora atual
    now = timezone.now()
    
    # Buscar tenant associado ao usuário atual
    try:
        tenant = Tenant.objects.get(usuario=request.user)
        
        # Contagens básicas
        times_count = Time.objects.filter(tenant=tenant).count()
        jogadores_count = Jogador.objects.filter(tenant=tenant).count()
        campeonatos_count = Campeonato.objects.filter(tenant=tenant).count()
        
        # Informações adicionais
        campeonatos = Campeonato.objects.filter(tenant=tenant).order_by('data_inicio')[:5]
        
        # Buscar próximas partidas (partidas que ainda não aconteceram)
        proximas_partidas = Partida.objects.filter(
            Q(rodada__campeonato__tenant=tenant) & 
            Q(data_hora__gt=now) & 
            ~Q(encerrada=True)
        ).order_by('data_hora')[:5]
        
    except Tenant.DoesNotExist:
        # Se não houver tenant, definir valores como vazios
        times_count = 0
        jogadores_count = 0
        campeonatos_count = 0
        campeonatos = []
        proximas_partidas = []
    
    context = {
        'times_count': times_count,
        'jogadores_count': jogadores_count,
        'campeonatos_count': campeonatos_count,
        'campeonatos': campeonatos,
        'proximas_partidas': proximas_partidas,
    }
    
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'adminpanel/perfil.html', {'form': form})


@login_required
def alterar_senha_view(request):
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('perfil')
    else:
        form = AlterarSenhaForm(request.user)
    
    return render(request, 'adminpanel/alterar_senha.html', {'form': form})


def logout_view(request, next_page=None):
    """Função de logout personalizada"""
    logout(request)
    if next_page:
        return HttpResponseRedirect(next_page)
    return redirect('/')
