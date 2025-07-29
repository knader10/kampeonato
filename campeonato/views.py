from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from .models import *
from adminpanel.models import Tenant
from .planos import PlanoManager, get_usuario_plano_atual, get_usuario_assinatura_info
import secrets
import string
import math
import random
from django.utils import timezone


def painel_registro(request):
    """View de registro de usuário para o painel SAAS"""
    from adminpanel.forms import RegistroForm
    from adminpanel.models import Usuario, Tenant
    from django.contrib.auth import login
    from django.utils.text import slugify
    from django.db import transaction
    
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
                # Salvar o ID do tenant na sessão
                request.session['tenant_id'] = tenant.id

            login(request, user)
            return redirect('campeonato:dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegistroForm()
    return render(request, 'adminpanel/registro.html', {'form': form, 'title': 'Criar Conta'})


from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from .models import *
from adminpanel.models import Tenant
import secrets
import string
from django.utils import timezone


def get_tenant_for_user(request):
    """Função auxiliar para obter o tenant do usuário atual"""
    from adminpanel.models import Tenant
    
    # Se for superuser, buscar tenant pela sessão
    if request.user.is_superuser and request.session.get('tenant_id'):
        tenant_id = request.session.get('tenant_id')
        return Tenant.objects.get(id=tenant_id)
    else:
        # Caso contrário, buscar tenant pelo usuário
        return Tenant.objects.get(usuario=request.user)


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


def campeonato_publico(request, codigo_publico):
    """Página pública de um campeonato específico"""
    try:
        campeonato = get_object_or_404(Campeonato, codigo_publico=codigo_publico)
    except:
        raise Http404("Campeonato não encontrado")
    
    # Buscar dados relacionados (igual view de gerenciamento)
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    times_campeonato = campeonato.times.all().select_related('time')
    rodadas_campeonato = campeonato.rodadas.all().prefetch_related(
        'partidas__time_mandante__time', 'partidas__time_visitante__time'
    ).order_by('numero')
    total_jogadores = sum(tc.jogadores.count() for tc in times_campeonato)
    classificacao_geral = calcular_classificacao(campeonato)
    classificacao_grupos = []
    artilharia = calcular_artilharia(campeonato)
    assistencias = calcular_assistencias(campeonato)
    cartoes_amarelos = calcular_cartoes_amarelos(campeonato)
    cartoes_vermelhos = calcular_cartoes_vermelhos(campeonato)
    if campeonato.tipo_formato == 'misto' and campeonato.num_grupos and campeonato.num_grupos > 1:
        classificacao_grupos = calcular_classificacao_por_grupos(campeonato)

    # Serialização expert para rodadas e partidas (carrossel estilo Globo Esporte)
    rodadas_list = []
    for rodada in rodadas_campeonato:
        partidas = []
        for partida in rodada.partidas.all():
            partidas.append({
                'id': partida.id,
                'time_mandante_nome': partida.time_mandante.time.nome,
                'time_mandante_escudo': partida.time_mandante.time.escudo.url if getattr(partida.time_mandante.time, 'escudo', None) else '',
                'placar_mandante': partida.placar_mandante,
                'time_visitante_nome': partida.time_visitante.time.nome,
                'time_visitante_escudo': partida.time_visitante.time.escudo.url if getattr(partida.time_visitante.time, 'escudo', None) else '',
                'placar_visitante': partida.placar_visitante,
                'data_hora': partida.data_hora.strftime('%d/%m %H:%M') if partida.data_hora else '',
                'local': partida.local or '',
                'status_display': partida.get_status_display() if hasattr(partida, 'get_status_display') else '',
            })
        rodadas_list.append({
            'id': rodada.id,
            'nome_exibicao': rodada.get_nome_exibicao() if hasattr(rodada, 'get_nome_exibicao') else f'Rodada {rodada.numero}',
            'numero': rodada.numero,
            'partidas': partidas,
        })

    context = {
        'campeonato': campeonato,
        'times_campeonato': times_campeonato,
        'rodadas_campeonato': rodadas_campeonato,
        'rodadas': rodadas_list,
        'rodadas_json': json.dumps(rodadas_list, cls=DjangoJSONEncoder),
        'total_jogadores': total_jogadores,
        'classificacao_geral': classificacao_geral,
        'classificacao_grupos': classificacao_grupos,
        'artilharia': artilharia,
        'assistencias': assistencias,
        'cartoes_amarelos': cartoes_amarelos,
        'cartoes_vermelhos': cartoes_vermelhos,
        'title': f'{campeonato.nome} - KAMPEONATO',
    }
    return render(request, 'public/campeonato_detail.html', context)


def calcular_classificacao_campeonato(campeonato):
    """Calcula a classificação do campeonato"""
    from collections import defaultdict
    
    classificacao = defaultdict(lambda: {
        'time': None,
        'jogos': 0,
        'vitorias': 0,
        'empates': 0,
        'derrotas': 0,
        'gols_pro': 0,
        'gols_contra': 0,
        'saldo_gols': 0,
        'pontos': 0
    })
    
    # Buscar todas as partidas finalizadas
    partidas = Partida.objects.filter(
        rodada__campeonato=campeonato,
        status='finalizada'
    ).select_related('time_mandante', 'time_visitante')
    
    for partida in partidas:
        # Time mandante
        time_mandante = partida.time_mandante
        stats_mandante = classificacao[time_mandante.id]
        stats_mandante['time'] = time_mandante
        stats_mandante['jogos'] += 1
        stats_mandante['gols_pro'] += partida.placar_mandante or 0
        stats_mandante['gols_contra'] += partida.placar_visitante or 0
        
        # Time visitante
        time_visitante = partida.time_visitante
        stats_visitante = classificacao[time_visitante.id]
        stats_visitante['time'] = time_visitante
        stats_visitante['jogos'] += 1
        stats_visitante['gols_pro'] += partida.placar_visitante or 0
        stats_visitante['gols_contra'] += partida.placar_mandante or 0
        
        # Resultado
        if partida.placar_mandante > partida.placar_visitante:
            # Vitória do mandante
            stats_mandante['vitorias'] += 1
            stats_mandante['pontos'] += 3
            stats_visitante['derrotas'] += 1
        elif partida.placar_visitante > partida.placar_mandante:
            # Vitória do visitante
            stats_visitante['vitorias'] += 1
            stats_visitante['pontos'] += 3
            stats_mandante['derrotas'] += 1
        else:
            # Empate
            stats_mandante['empates'] += 1
            stats_mandante['pontos'] += 1
            stats_visitante['empates'] += 1
            stats_visitante['pontos'] += 1
    
    # Calcular saldo de gols e ordenar
    for stats in classificacao.values():
        stats['saldo_gols'] = stats['gols_pro'] - stats['gols_contra']
    
    # Ordenar por pontos, saldo de gols, gols pró
    return sorted(
        classificacao.values(),
        key=lambda x: (-x['pontos'], -x['saldo_gols'], -x['gols_pro'])
    )



# ========== ÁREA ADMINISTRATIVA ==========

def admin_login(request):
    """Login do sistema administrativo"""
    if request.user.is_authenticated:
        # Se já está autenticado e é superuser, mas não escolheu tenant, redireciona para escolha
        if request.user.is_superuser and not request.session.get('tenant_id'):
            return redirect('campeonato:escolher_tenant')
        return redirect('campeonato:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # Se for superuser, redireciona para escolha de tenant
            if user.is_superuser:
                return redirect('campeonato:escolher_tenant')
            # Se não, salva tenant do usuário na sessão
            try:
                from adminpanel.models import Tenant
                tenant = Tenant.objects.get(usuario=user)
                request.session['tenant_id'] = tenant.id
                return redirect('campeonato:dashboard')
            except Tenant.DoesNotExist:
                messages.error(request, 'Usuário não possui tenant associado.')
                logout(request)  # Deslogar o usuário para evitar loops
                return redirect('campeonato:painel_login')
        else:
            messages.error(request, 'Email ou senha inválidos.')
    return render(request, 'auth/login.html', {'title': 'Login'})


def escolher_tenant(request):
    """View para superuser escolher o tenant que deseja acessar"""
    from adminpanel.models import Tenant
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('campeonato:painel_login')
    tenants = Tenant.objects.all().order_by('nome')
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        if tenant_id and tenants.filter(id=tenant_id).exists():
            request.session['tenant_id'] = int(tenant_id)
            return redirect('campeonato:dashboard')
        else:
            messages.error(request, 'Selecione um tenant válido.')
    return render(request, 'auth/escolher_tenant.html', {'tenants': tenants, 'title': 'Escolher Tenant'})


def admin_logout(request):
    """Logout do sistema"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('campeonato:index')


@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    # Buscar tenant do usuário
    try:
        tenant = get_tenant_for_user(request)
        
        # Estatísticas
        total_campeonatos = Campeonato.objects.filter(tenant=tenant).count()
        total_times = Time.objects.filter(tenant=tenant).count()
        total_jogadores = Jogador.objects.filter(tenant=tenant).count()
        campeonatos_ativos = Campeonato.objects.filter(
            tenant=tenant,
            data_inicio__lte=timezone.now().date()
        ).count()
        
        # Campeonatos recentes
        campeonatos_recentes = Campeonato.objects.filter(tenant=tenant).order_by('-data_inicio')[:5]
        
        # Próximos jogos (apenas com data definida)
        proximos_jogos = Partida.objects.filter(
            rodada__campeonato__tenant=tenant,
            status__in=['nao_iniciada', 'em_andamento'],
            data_hora__isnull=False
        ).select_related('time_mandante__time', 'time_visitante__time', 'rodada__campeonato').order_by('data_hora')[:10]
        
        # Status dos campeonatos
        campeonatos_status = Campeonato.objects.filter(tenant=tenant).order_by('-data_inicio')[:8]
        
        plano_manager = PlanoManager()
        planos_data = plano_manager.get_planos_data()
        assinatura_info = get_usuario_assinatura_info(request.user)
        if assinatura_info:
            plano_atual_id = get_usuario_plano_atual(request.user)
        else:
            plano_atual_id = None

        context = {
            'stats': {
                'total_campeonatos': total_campeonatos,
                'total_times': total_times,
                'total_jogadores': total_jogadores,
                'campeonatos_ativos': campeonatos_ativos,
            },
            'times_count': total_times,
            'jogadores_count': total_jogadores,
            'campeonatos_count': total_campeonatos,
            'campeonatos_ativos_count': campeonatos_ativos,
            'campeonatos_recentes': campeonatos_recentes,
            'proximos_jogos': proximos_jogos,
            'campeonatos_status': campeonatos_status,
            'planos_data': planos_data,
            'assinatura_info': assinatura_info,
            'title': 'Dashboard'
        }
        # Só adiciona plano_atual_id se houver assinatura
        if assinatura_info:
            context['plano_atual_id'] = plano_atual_id
        return render(request, 'adminpanel/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Erro ao carregar dashboard: {str(e)}')
        return redirect('campeonato:admin_logout')


@login_required
def configuracoes(request):
    """View de configurações do sistema com gerenciamento de planos"""
    try:
        tenant = get_tenant_for_user(request)
        plano_manager = PlanoManager()
        
        # Obter dados dos planos
        planos_data = plano_manager.get_planos_data()
        
        # Obter informações da assinatura atual do usuário
        assinatura_info = get_usuario_assinatura_info(request.user)
        if assinatura_info:
            plano_atual_id = get_usuario_plano_atual(request.user)
        else:
            plano_atual_id = None
        
        context = {
            'tenant': tenant,
            'planos_data': planos_data,
            'assinatura_info': assinatura_info,
            'plano_atual_id': plano_atual_id,
            'title': 'Configurações de Assinatura'
        }
        return render(request, 'adminpanel/configuracoes.html', context)
    except Exception as e:
        messages.error(request, f'Erro ao carregar configurações: {str(e)}')
        return redirect('campeonato:dashboard')


@login_required
def api_planos_data(request):
    """API endpoint para retornar dados dos planos em JSON"""
    try:
        plano_manager = PlanoManager()
        planos_data = plano_manager.get_planos_data()
        
        # Adicionar informações do usuário atual
        plano_atual_id = get_usuario_plano_atual(request.user)
        assinatura_info = get_usuario_assinatura_info(request.user)
        
        response_data = {
            'planos_data': planos_data,
            'usuario': {
                'plano_atual_id': plano_atual_id,
                'assinatura_info': assinatura_info
            }
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Placeholder para outras views administrativas que já existem
@login_required 
def campeonatos_list(request):
    """Lista campeonatos do tenant"""
    try:
        from adminpanel.models import Tenant
        tenant = get_tenant_for_user(request)
        campeonatos = Campeonato.objects.filter(tenant=tenant).order_by('-data_inicio')
        return render(request, 'campeonato/campeonatos_list.html', {
            'campeonatos': campeonatos, 
            'title': 'Campeonatos'
        })
    except Exception as e:
        messages.error(request, f'Erro ao listar campeonatos: {str(e)}')
        return redirect('campeonato:dashboard')

@login_required
def campeonato_create(request):
    """Criar novo campeonato"""
    from .forms import CampeonatoForm
    
    try:
        tenant = get_tenant_for_user(request)
        
        if request.method == 'POST':
            form = CampeonatoForm(request.POST)
            if form.is_valid():
                campeonato = form.save(commit=False)
                campeonato.tenant = tenant
                # Gerar código público único
                import secrets
                import string
                campeonato.codigo_publico = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                campeonato.save()
                messages.success(request, 'Campeonato criado com sucesso!')
                return redirect('campeonato:campeonato_detail', pk=campeonato.id)
            else:
                # Mostrar erros de validação
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Erro no campo {field}: {error}')
        else:
            form = CampeonatoForm()
        
        return render(request, 'campeonato/campeonato_form.html', {
            'form': form,
            'title': 'Criar Campeonato'
        })
    except Exception as e:
        messages.error(request, f'Erro ao criar campeonato: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def campeonato_detail(request, pk):
    """Detalhes do campeonato"""
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=pk, tenant=tenant)
        
        context = {
            'campeonato': campeonato,
            'title': f'{campeonato.nome} - Detalhes'
        }
        return render(request, 'campeonato/campeonato_detail.html', context)
    except Exception as e:
        messages.error(request, f'Erro ao carregar campeonato: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def campeonato_update(request, pk):
    """Editar campeonato"""
    from .forms import CampeonatoForm
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            form = CampeonatoForm(request.POST, instance=campeonato)
            if form.is_valid():
                form.save()
                messages.success(request, 'Campeonato atualizado com sucesso!')
                return redirect('campeonato:campeonato_detail', pk=campeonato.id)
        else:
            form = CampeonatoForm(instance=campeonato)
        
        return render(request, 'campeonato/campeonato_form.html', {
            'form': form,
            'campeonato': campeonato,
            'title': f'Editar {campeonato.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao editar campeonato: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def campeonato_delete(request, pk):
    """Deletar campeonato"""
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            nome_campeonato = campeonato.nome
            campeonato.delete()
            messages.success(request, f'Campeonato "{nome_campeonato}" foi excluído com sucesso!')
            return redirect('campeonato:campeonatos_list')
        
        return render(request, 'campeonato/campeonato_confirm_delete.html', {
            'campeonato': campeonato,
            'title': f'Excluir {campeonato.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao excluir campeonato: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def campeonato_gerenciar(request, pk):
    """Gerenciar campeonato - Times, Jogadores e Profissionais"""
    from .forms import TimeCampeonatoForm, VincularJogadorForm, ProfissionalForm
    from .models import TimeCampeonato, JogadorTimeCampeonato, ProfissionalCampeonato
    from django.db.models import Count, Prefetch, Q
    from django.db import models
    
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=pk, tenant=tenant)
    
    # Verificar se o campeonato está finalizado
    campeonato_finalizado = campeonato.status == 'finalizado'
    
    # Se campeonato finalizado e é uma requisição POST, bloquear alterações
    if campeonato_finalizado and request.method == 'POST':
        messages.error(request, 'Não é possível fazer alterações em um campeonato finalizado.')
        return redirect('campeonato:campeonato_gerenciar', pk=pk)
    
    # Otimizar busca de times vinculados com contagem de jogadores
    times_campeonato = TimeCampeonato.objects.filter(
        campeonato=campeonato
    ).select_related('time').prefetch_related(
        Prefetch(
            'jogadores',
            queryset=JogadorTimeCampeonato.objects.select_related('jogador').filter(ativo=True),
            to_attr='jogadores_ativos'
        )
    ).annotate(
        jogadores_count=Count('jogadores', filter=Q(jogadores__ativo=True))
    )
    
    # Pré-carregar jogadores disponíveis para cada time (limitado para performance)
    for time_campeonato in times_campeonato:
        jogadores_vinculados_ids = [jt.jogador.id for jt in time_campeonato.jogadores_ativos]
        time_campeonato.jogadores_disponiveis = Jogador.objects.filter(
            tenant=tenant
        ).exclude(
            id__in=jogadores_vinculados_ids
        ).only('id', 'nome', 'cidade', 'telefone', 'foto')[:30]  # Limitar a 30
    
    # Buscar times disponíveis de forma otimizada
    times_vinculados_ids = list(times_campeonato.values_list('time_id', flat=True))
    times_disponiveis = Time.objects.filter(
        tenant=tenant
    ).exclude(
        id__in=times_vinculados_ids
    ).only('id', 'nome', 'cidade', 'escudo')[:50]  # Limitar a 50 para performance
    
    # Otimizar busca de profissionais vinculados
    profissionais_campeonato = ProfissionalCampeonato.objects.filter(
        campeonato=campeonato
    ).select_related('profissional').only(
        'id', 'profissional__id', 'profissional__nome', 'profissional__cpf',
        'profissional__cidade', 'profissional__federacao', 'profissional__chave_pix',
        'profissional__tipo_chave_pix', 'profissional__liga', 'profissional__telefone'
    )
    
    # Buscar profissionais disponíveis de forma otimizada
    profissionais_vinculados_ids = list(profissionais_campeonato.values_list('profissional_id', flat=True))
    profissionais_disponiveis = Profissional.objects.filter(
        tenant=tenant
    ).exclude(
        id__in=profissionais_vinculados_ids
    ).only('id', 'nome', 'cpf', 'cidade', 'federacao')[:50]  # Limitar a 50 para performance
    
    # Buscar rodadas de forma otimizada
    rodadas_campeonato = campeonato.rodadas.all().prefetch_related(
        'partidas__time_mandante__time', 
        'partidas__time_visitante__time'
    ).order_by('numero')
    
    # Adicionar informação sobre status das rodadas
    tem_partidas_finalizadas = False
    for rodada in rodadas_campeonato:
        partidas = rodada.partidas.all()
        total_partidas = len(partidas)
        partidas_finalizadas = sum(1 for p in partidas if p.status == 'finalizada')
        rodada.todas_finalizadas = total_partidas > 0 and partidas_finalizadas == total_partidas
        rodada.total_partidas = total_partidas
        rodada.partidas_finalizadas = partidas_finalizadas
        
        # Verificar se há partidas finalizadas no campeonato
        if partidas_finalizadas > 0:
            tem_partidas_finalizadas = True
    
    # Calcular estatísticas de forma otimizada
    total_jogadores = sum(getattr(tc, 'jogadores_count', 0) for tc in times_campeonato)
    
    # Calcular classificação e estatísticas para a aba Geral
    classificacao_geral = calcular_classificacao(campeonato)
    classificacao_grupos = []
    artilharia = calcular_artilharia(campeonato)
    assistencias = calcular_assistencias(campeonato)
    cartoes_amarelos = calcular_cartoes_amarelos(campeonato)
    cartoes_vermelhos = calcular_cartoes_vermelhos(campeonato)
    
    # Se for campeonato misto com grupos, calcular classificação por grupo
    if campeonato.tipo_formato == 'misto' and campeonato.num_grupos and campeonato.num_grupos > 1:
        classificacao_grupos = calcular_classificacao_por_grupos(campeonato)
    
    # Processar ação de vincular time
    if request.method == 'POST' and 'vincular_time' in request.POST:
        form_time = TimeCampeonatoForm(request.POST, tenant=tenant)
        if form_time.is_valid():
            time_campeonato = form_time.save(commit=False)
            time_campeonato.campeonato = campeonato
            time_campeonato.save()
            messages.success(request, f'Time {time_campeonato.time.nome} vinculado ao campeonato!')
            return redirect('campeonato:campeonato_gerenciar', pk=pk)
    elif request.method == 'POST' and 'time_existente' in request.POST:
        time_id = request.POST.get('time_existente')
        time = get_object_or_404(Time, pk=time_id, tenant=tenant)
        
        # Verificar se o time já está vinculado
        if TimeCampeonato.objects.filter(time=time, campeonato=campeonato).exists():
            messages.warning(request, f'Time {time.nome} já está vinculado ao campeonato!')
        else:
            TimeCampeonato.objects.create(time=time, campeonato=campeonato)
            messages.success(request, f'Time {time.nome} vinculado ao campeonato!')
        return redirect('campeonato:campeonato_gerenciar', pk=pk)
    else:
        form_time = TimeCampeonatoForm(tenant=tenant)
    
    # Formulário para profissionais
    profissional_form = ProfissionalForm()
    
    context = {
        'campeonato': campeonato,
        'campeonato_finalizado': campeonato_finalizado,
        'tem_partidas_finalizadas': tem_partidas_finalizadas,
        'times_campeonato': times_campeonato,
        'times_disponiveis': times_disponiveis,
        'form_time': form_time,
        'profissionais_campeonato': profissionais_campeonato,
        'profissionais_disponiveis': profissionais_disponiveis,
        'profissional_form': profissional_form,
        'profissionais_vinculados_ids': list(profissionais_vinculados_ids),
        'rodadas_campeonato': rodadas_campeonato,
        'total_jogadores': total_jogadores,
        'classificacao_geral': classificacao_geral,
        'classificacao_grupos': classificacao_grupos,
        'artilharia': artilharia,
        'assistencias': assistencias,
        'cartoes_amarelos': cartoes_amarelos,
        'cartoes_vermelhos': cartoes_vermelhos,
        'title': f'Gerenciar {campeonato.nome}'
    }
    
    return render(request, 'campeonato/campeonato_gerenciar.html', context)

@login_required
def times_list(request):
    """Lista times do tenant"""
    try:
        tenant = get_tenant_for_user(request)
        
        # Buscar times com os vínculos de campeonatos
        times = Time.objects.filter(tenant=tenant).prefetch_related(
            'participacoes__campeonato'
        ).order_by('nome')
        
        return render(request, 'campeonato/times_list.html', {
            'times': times, 
            'title': 'Times'
        })
    except Exception as e:
        messages.error(request, f'Erro ao listar times: {str(e)}')
        return redirect('campeonato:dashboard')

@login_required
def time_create(request):
    """Criar novo time"""
    from .forms import TimeForm
    
    try:
        tenant = get_tenant_for_user(request)
        
        if request.method == 'POST':
            form = TimeForm(request.POST, request.FILES)
            if form.is_valid():
                time = form.save(commit=False)
                time.tenant = tenant
                time.save()
                messages.success(request, 'Time criado com sucesso!')
                return redirect('campeonato:time_detail', pk=time.id)
        else:
            form = TimeForm()
        
        return render(request, 'campeonato/time_form.html', {
            'form': form,
            'title': 'Criar Time'
        })
    except Exception as e:
        messages.error(request, f'Erro ao criar time: {str(e)}')
        return redirect('campeonato:times_list')

@login_required
def time_detail(request, pk):
    """Detalhes do time"""
    try:
        tenant = get_tenant_for_user(request)
        time = get_object_or_404(Time, pk=pk, tenant=tenant)
        
        # Buscar campeonatos onde este time está vinculado
        from .models import TimeCampeonato
        vinculos_campeonatos = TimeCampeonato.objects.filter(
            time=time
        ).select_related('campeonato').order_by('-data_inscricao')
        
        context = {
            'time': time,
            'vinculos_campeonatos': vinculos_campeonatos,
            'title': f'{time.nome} - Detalhes'
        }
        return render(request, 'campeonato/time_detail.html', context)
    except Exception as e:
        messages.error(request, f'Erro ao carregar time: {str(e)}')
        return redirect('campeonato:times_list')

@login_required
def time_update(request, pk):
    """Editar time"""
    from .forms import TimeForm
    
    try:
        tenant = get_tenant_for_user(request)
        time = get_object_or_404(Time, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            form = TimeForm(request.POST, request.FILES, instance=time)
            if form.is_valid():
                form.save()
                messages.success(request, 'Time atualizado com sucesso!')
                return redirect('campeonato:time_detail', pk=time.id)
        else:
            form = TimeForm(instance=time)
        
        return render(request, 'campeonato/time_form.html', {
            'form': form,
            'time': time,
            'title': f'Editar {time.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao editar time: {str(e)}')
        return redirect('campeonato:times_list')

@login_required
def time_delete(request, pk):
    """Deletar time"""
    try:
        tenant = get_tenant_for_user(request)
        time = get_object_or_404(Time, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            nome_time = time.nome
            time.delete()
            messages.success(request, f'Time "{nome_time}" foi excluído com sucesso!')
            return redirect('campeonato:times_list')
        
        return render(request, 'campeonato/time_confirm_delete.html', {
            'time': time,
            'title': f'Excluir {time.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao excluir time: {str(e)}')
        return redirect('campeonato:times_list')

@login_required
def jogadores_list(request):
    """Lista jogadores do tenant com paginação e pesquisa"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    try:
        tenant = get_tenant_for_user(request)
        
        # Obter parâmetro de pesquisa
        search_query = request.GET.get('search', '').strip()
        
        # Filtrar jogadores
        jogadores = Jogador.objects.filter(tenant=tenant)
        
        # Aplicar filtro de pesquisa se fornecido
        if search_query:
            jogadores = jogadores.filter(
                Q(nome__icontains=search_query) |
                Q(cidade__icontains=search_query) |
                Q(logradouro__icontains=search_query) |
                Q(bairro__icontains=search_query)
            )
        
        # Ordenar por nome
        jogadores = jogadores.order_by('nome')
        
        # Implementar paginação (20 jogadores por página)
        paginator = Paginator(jogadores, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'jogadores': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'total_count': paginator.count,
            'title': 'Jogadores'
        }
        
        return render(request, 'campeonato/jogadores_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao listar jogadores: {str(e)}')
        return redirect('campeonato:dashboard')

@login_required
def jogador_create(request):
    """Criar novo jogador"""
    from .forms import JogadorForm
    try:
        tenant = get_tenant_for_user(request)
        if request.method == 'POST':
            print(f"DEBUG: POST recebido para criar jogador. Dados: {request.POST}")
            form = JogadorForm(request.POST, request.FILES, tenant=tenant)
            if form.is_valid():
                print("DEBUG: Formulário válido, salvando jogador...")
                jogador = form.save(commit=False)
                jogador.tenant = tenant
                jogador.save()
                print(f"DEBUG: Jogador salvo com sucesso: {jogador.nome} (ID: {jogador.id})")
                messages.success(request, f'Jogador "{jogador.nome}" criado com sucesso!')
                print("DEBUG: Redirecionando para lista de jogadores...")
                return redirect('campeonato:jogadores_list')
            else:
                print(f"DEBUG: Formulário inválido. Erros: {form.errors}")
        else:
            form = JogadorForm(tenant=tenant)
        return render(request, 'campeonato/jogador_form.html', {
            'form': form,
            'title': 'Criar Jogador'
        })
    except Exception as e:
        print(f"DEBUG: Exceção capturada: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Erro ao criar jogador: {str(e)}')
        return redirect('campeonato:jogadores_list')

@login_required
def jogador_detail(request, pk):
    """Detalhes do jogador"""
    try:
        tenant = get_tenant_for_user(request)
        jogador = get_object_or_404(Jogador, pk=pk, tenant=tenant)
        
        context = {
            'jogador': jogador,
            'title': f'{jogador.nome} - Detalhes'
        }
        return render(request, 'campeonato/jogador_detail.html', context)
    except Exception as e:
        messages.error(request, f'Erro ao carregar jogador: {str(e)}')
        return redirect('campeonato:jogadores_list')

@login_required
def jogador_update(request, pk):
    """Editar jogador"""
    from .forms import JogadorForm
    
    try:
        tenant = get_tenant_for_user(request)
        jogador = get_object_or_404(Jogador, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            form = JogadorForm(request.POST, request.FILES, instance=jogador, tenant=tenant)
            if form.is_valid():
                form.save()
                messages.success(request, 'Jogador atualizado com sucesso!')
                return redirect('campeonato:jogador_detail', pk=jogador.id)
        else:
            form = JogadorForm(instance=jogador, tenant=tenant)
        
        return render(request, 'campeonato/jogador_form.html', {
            'form': form,
            'jogador': jogador,
            'title': f'Editar {jogador.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao editar jogador: {str(e)}')
        return redirect('campeonato:jogadores_list')

@login_required
def jogador_delete(request, pk):
    """Deletar jogador"""
    try:
        tenant = get_tenant_for_user(request)
        jogador = get_object_or_404(Jogador, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            nome_jogador = jogador.nome
            jogador.delete()
            messages.success(request, f'Jogador "{nome_jogador}" foi excluído com sucesso!')
            return redirect('campeonato:jogadores_list')
        
        return render(request, 'campeonato/jogador_confirm_delete.html', {
            'jogador': jogador,
            'title': f'Excluir {jogador.nome}'
        })
    except Exception as e:
        messages.error(request, f'Erro ao excluir jogador: {str(e)}')
        return redirect('campeonato:jogadores_list')

@login_required
def profissionais_list(request):
    """Listar profissionais"""
    try:
        tenant = get_tenant_for_user(request)
        profissionais = Profissional.objects.filter(tenant=tenant)
        
        # Busca
        search = request.GET.get('search')
        if search:
            profissionais = profissionais.filter(
                Q(nome__icontains=search) | 
                Q(cidade__icontains=search) |
                Q(federacao__icontains=search)
            )
        
        # Paginação
        paginator = Paginator(profissionais, 20)
        page_number = request.GET.get('page')
        profissionais = paginator.get_page(page_number)
        
        context = {
            'profissionais': profissionais,
            'search': search,
            'title': 'Profissionais'
        }
        
        return render(request, 'campeonato/profissionais_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:dashboard')

@login_required
def profissional_create(request):
    """Criar profissional"""
    from .forms import ProfissionalForm
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato_id = request.GET.get('campeonato')
        
        if request.method == 'POST':
            form = ProfissionalForm(request.POST)
            if form.is_valid():
                profissional = form.save(commit=False)
                profissional.tenant = tenant
                profissional.save()
                messages.success(request, f'Profissional {profissional.nome} criado com sucesso!')
                
                # Redirecionar para o campeonato se especificado
                if campeonato_id:
                    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
                return redirect('campeonato:profissionais_list')
            else:
                # Formulário inválido - adicionar mensagem de erro geral
                messages.error(request, 'Por favor, corrija os erros abaixo.')
        else:
            form = ProfissionalForm()
        
        context = {
            'form': form,
            'campeonato_id': campeonato_id,
            'title': 'Novo Profissional'
        }
        
        return render(request, 'campeonato/profissional_form.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        if campeonato_id:
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
        return redirect('campeonato:dashboard')

@login_required
def profissional_detail(request, pk):
    """Detalhe do profissional"""
    try:
        tenant = get_tenant_for_user(request)
        profissional = get_object_or_404(Profissional, pk=pk, tenant=tenant)
        
        context = {
            'profissional': profissional,
            'title': profissional.nome
        }
        
        return render(request, 'campeonato/profissional_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:profissionais_list')

@login_required
def profissional_update(request, pk):
    """Editar profissional"""
    from .forms import ProfissionalForm
    
    try:
        tenant = get_tenant_for_user(request)
        profissional = get_object_or_404(Profissional, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            form = ProfissionalForm(request.POST, instance=profissional)
            if form.is_valid():
                form.save()
                messages.success(request, f'Profissional {profissional.nome} atualizado com sucesso!')
                return redirect('campeonato:profissional_detail', pk=pk)
        else:
            form = ProfissionalForm(instance=profissional)
        
        context = {
            'form': form,
            'profissional': profissional,
            'title': f'Editar {profissional.nome}'
        }
        
        return render(request, 'campeonato/profissional_form.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:profissionais_list')

@login_required
def profissional_delete(request, pk):
    """Deletar profissional"""
    try:
        tenant = get_tenant_for_user(request)
        profissional = get_object_or_404(Profissional, pk=pk, tenant=tenant)
        
        if request.method == 'POST':
            nome = profissional.nome
            profissional.delete()
            messages.success(request, f'Profissional {nome} removido com sucesso!')
            return redirect('campeonato:profissionais_list')
        
        context = {
            'profissional': profissional,
            'title': f'Remover {profissional.nome}'
        }
        
        return render(request, 'campeonato/profissional_confirm_delete.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:profissionais_list')

@login_required
def vincular_profissional_campeonato(request, campeonato_pk):
    """Vincular profissional ao campeonato"""
    from .forms import ProfissionalForm
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        
        if request.method == 'POST':
            # Verificar se é profissional existente ou novo
            if 'profissional_existente' in request.POST:
                profissional_id = request.POST.get('profissional_existente')
                profissional = get_object_or_404(Profissional, pk=profissional_id, tenant=tenant)
                
                # Verificar se já está vinculado
                if ProfissionalCampeonato.objects.filter(profissional=profissional, campeonato=campeonato).exists():
                    messages.warning(request, f'Profissional {profissional.nome} já está vinculado ao campeonato!')
                else:
                    ProfissionalCampeonato.objects.create(profissional=profissional, campeonato=campeonato)
                    messages.success(request, f'Profissional {profissional.nome} vinculado ao campeonato!')
            else:
                # Criar novo profissional
                print(f"DEBUG: Dados recebidos: {request.POST}")
                form = ProfissionalForm(request.POST)
                
                if form.is_valid():
                    print("DEBUG: Formulário válido, salvando profissional...")
                    profissional = form.save(commit=False)
                    profissional.tenant = tenant
                    profissional.save()
                    print(f"DEBUG: Profissional salvo: {profissional.nome} (ID: {profissional.id})")
                    
                    # Vincular ao campeonato
                    ProfissionalCampeonato.objects.create(profissional=profissional, campeonato=campeonato)
                    messages.success(request, f'Profissional {profissional.nome} criado e vinculado ao campeonato!')
                else:
                    print(f"DEBUG: Formulário inválido. Erros: {form.errors}")
                    # Melhor tratamento de erros
                    if form.errors:
                        error_messages = []
                        for field, errors in form.errors.items():
                            field_label = form.fields[field].label or field
                            for error in errors:
                                error_messages.append(f"{field_label}: {error}")
                        
                        messages.error(request, "Erro ao cadastrar profissional:")
                        for error_msg in error_messages:
                            messages.error(request, error_msg)
                    else:
                        messages.error(request, 'Erro desconhecido ao validar o formulário.')
        
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
        
    except Exception as e:
        print(f"DEBUG: Exceção capturada: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def desvincular_profissional_campeonato(request, campeonato_pk, vinculo_pk):
    """Desvincular profissional do campeonato"""
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        vinculo = get_object_or_404(ProfissionalCampeonato, pk=vinculo_pk, campeonato=campeonato)
        
        if request.method == 'POST':
            profissional_nome = vinculo.profissional.nome
            vinculo.delete()
            messages.success(request, f'Profissional {profissional_nome} desvinculado do campeonato!')
        
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:campeonatos_list')

@login_required
def editar_profissional_campeonato(request, campeonato_pk):
    """Editar profissional via modal no campeonato"""
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        
        if request.method == 'POST':
            profissional_id = request.POST.get('profissional_id')
            profissional = get_object_or_404(Profissional, pk=profissional_id, tenant=tenant)
            
            # Atualizar dados do profissional
            profissional.nome = request.POST.get('nome', profissional.nome)
            profissional.cpf = request.POST.get('cpf', profissional.cpf)
            profissional.cidade = request.POST.get('cidade', profissional.cidade)
            profissional.federacao = request.POST.get('federacao', profissional.federacao)
            profissional.liga = request.POST.get('liga', profissional.liga)
            profissional.telefone = request.POST.get('telefone', profissional.telefone)
            profissional.chave_pix = request.POST.get('chave_pix', profissional.chave_pix)
            profissional.tipo_chave_pix = request.POST.get('tipo_chave_pix', profissional.tipo_chave_pix)
            
            profissional.save()
            messages.success(request, f'Profissional {profissional.nome} atualizado com sucesso!')
        
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('campeonato:campeonatos_list')

# ==================== API ====================

# API endpoints para AJAX
@login_required
def dashboard_stats(request):
    """Retorna estatísticas para o dashboard"""
    try:
        tenant = get_tenant_for_user(request)
    except:
        return JsonResponse({'error': 'Tenant não encontrado'}, status=400)
    
    stats = {
        'total_campeonatos': Campeonato.objects.filter(tenant=tenant).count(),
        'total_times': Time.objects.filter(tenant=tenant).count(),
        'total_jogadores': Jogador.objects.filter(tenant=tenant).count(),
        'campeonatos_ativos': Campeonato.objects.filter(
            tenant=tenant,
            data_inicio__lte=timezone.now().date()
        ).count(),
    }
    
    return JsonResponse(stats)

@login_required
def campeonatos_search(request):
    """Busca campeonatos por AJAX"""
    query = request.GET.get('q', '')
    try:
        tenant = get_tenant_for_user(request)
    except:
        return JsonResponse({'error': 'Tenant não encontrado'}, status=400)
    
    campeonatos = Campeonato.objects.filter(tenant=tenant)
    
    if query:
        campeonatos = campeonatos.filter(
            Q(nome__icontains=query) |
            Q(edicao__icontains=query) |
            Q(organizador__icontains=query)
        )
    
    campeonatos = campeonatos.order_by('-data_inicio')[:10]
    
    data = []
    for campeonato in campeonatos:
        data.append({
            'id': campeonato.id,
            'nome': campeonato.nome,
            'edicao': campeonato.edicao,
            'organizador': campeonato.organizador,
            'data_inicio': campeonato.data_inicio.strftime('%d/%m/%Y'),
            'esta_ativo': campeonato.esta_ativo,
        })
    
    return JsonResponse({'campeonatos': data})


@login_required
def perfil(request):
    """View de perfil do usuário"""
    from adminpanel.forms import PerfilForm
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('campeonato:perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'adminpanel/perfil.html', {'form': form})


@login_required
def alterar_senha(request):
    """View para alterar senha do usuário"""
    from adminpanel.forms import AlterarSenhaForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('campeonato:perfil')
    else:
        form = AlterarSenhaForm(request.user)
    
    return render(request, 'adminpanel/alterar_senha.html', {'form': form})


# Views adicionais para o template refatorado
@login_required
def jogadores_time(request, campeonato_pk, time_campeonato_pk):
    """View para listar e gerenciar jogadores de um time específico"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    time_campeonato = get_object_or_404(TimeCampeonato, pk=time_campeonato_pk, campeonato=campeonato)
    
    jogadores = time_campeonato.jogadores.filter(ativo=True)
    
    # Excluir jogadores já vinculados ao time da lista de disponíveis
    jogadores_vinculados_ids = jogadores.values_list('jogador_id', flat=True)
    jogadores_disponiveis = tenant.jogadores.exclude(id__in=jogadores_vinculados_ids)
    
    context = {
        'campeonato': campeonato,
        'time_campeonato': time_campeonato,
        'jogadores': jogadores,
        'jogadores_disponiveis': jogadores_disponiveis,
    }
    return render(request, 'campeonato/jogadores_time.html', context)


@login_required
def vincular_time_view(request, campeonato_pk):
    """View para vincular um time existente ao campeonato"""
    from django.utils import timezone
    from .models import Time, TimeCampeonato
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        times_disponiveis = tenant.times.exclude(
            id__in=campeonato.times.values_list('time_id', flat=True)
        )

        if request.method == 'POST':
            # Verificar se é time existente ou novo
            time_existente_id = request.POST.get('time_existente')
            
            if time_existente_id:
                # Vincular time existente
                print(f"DEBUG: Vinculando time existente ID: {time_existente_id}")
                time = get_object_or_404(Time, pk=time_existente_id, tenant=tenant)
                
                if not TimeCampeonato.objects.filter(campeonato=campeonato, time=time).exists():
                    TimeCampeonato.objects.create(
                        campeonato=campeonato,
                        time=time,
                        data_inscricao=timezone.now().date()
                    )
                    messages.success(request, f'Time {time.nome} vinculado com sucesso!')
                else:
                    messages.error(request, f'Time {time.nome} já está vinculado ao campeonato.')
            else:
                # Criar novo time
                print(f"DEBUG: Criando novo time com dados: {request.POST}")
                nome = request.POST.get('nome')
                cidade = request.POST.get('cidade')
                presidente = request.POST.get('presidente', '')
                campo_estadio = request.POST.get('campo_estadio', '')
                localizacao = request.POST.get('localizacao', '')
                
                if nome and cidade:
                    # Usar ano padrão (ano atual)
                    from datetime import date
                    ano_fundacao = date.today().year
                    
                    # Criar o time
                    time = Time.objects.create(
                        tenant=tenant,
                        nome=nome,
                        cidade=cidade,
                        ano_fundacao=ano_fundacao
                    )
                    
                    # Vincular ao campeonato com informações adicionais
                    TimeCampeonato.objects.create(
                        campeonato=campeonato,
                        time=time,
                        presidente=presidente,
                        campo_estadio=campo_estadio,
                        localizacao=localizacao,
                        data_inscricao=timezone.now().date()
                    )
                    messages.success(request, f'Time {time.nome} criado e vinculado com sucesso!')
                else:
                    messages.error(request, 'Nome e cidade são obrigatórios para criar um time.')
            
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)

        context = {
            'campeonato': campeonato,
            'times_disponiveis': times_disponiveis,
        }
        return render(request, 'campeonato/vincular_time.html', context)
        
    except Exception as e:
        print(f"DEBUG: Erro em vincular_time_view: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Erro ao vincular time: {str(e)}')
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def desvincular_time(request, campeonato_pk, time_campeonato_pk):
    """View para desvincular um time do campeonato"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    time_campeonato = get_object_or_404(TimeCampeonato, pk=time_campeonato_pk, campeonato=campeonato)
    
    if request.method == 'POST':
        time_nome = time_campeonato.time.nome
        time_campeonato.delete()
        messages.success(request, f'Time {time_nome} removido do campeonato com sucesso!')
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
    
    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def vincular_profissional_view(request, campeonato_pk):
    """View para vincular um profissional existente ao campeonato"""
    from django.utils import timezone
    from .models import ProfissionalCampeonato
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        profissionais_disponiveis = Profissional.objects.filter(tenant=tenant).exclude(
            id__in=campeonato.profissionais.values_list('profissional_id', flat=True)
        )
        
        if request.method == 'POST':
            profissional_id = request.POST.get('profissional_id')
            funcao = request.POST.get('funcao', '')
            profissional = get_object_or_404(Profissional, pk=profissional_id, tenant=tenant)
            
            # Verificar se o profissional já não está vinculado
            if not ProfissionalCampeonato.objects.filter(campeonato=campeonato, profissional=profissional).exists():
                ProfissionalCampeonato.objects.create(
                    campeonato=campeonato,
                    profissional=profissional,
                    funcao=funcao,
                    data_vinculacao=timezone.now().date()
                )
                messages.success(request, f'Profissional {profissional.nome} vinculado com sucesso!')
            else:
                messages.error(request, f'Profissional {profissional.nome} já está vinculado ao campeonato.')
            
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
        
        context = {
            'campeonato': campeonato,
            'profissionais_disponiveis': profissionais_disponiveis,
        }
        return render(request, 'campeonato/vincular_profissional.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao vincular profissional: {str(e)}')
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def desvincular_profissional(request, campeonato_pk, profissional_campeonato_pk):
    """View para desvincular um profissional do campeonato"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    profissional_campeonato = get_object_or_404(ProfissionalCampeonato, pk=profissional_campeonato_pk, campeonato=campeonato)
    
    if request.method == 'POST':
        profissional_nome = profissional_campeonato.profissional.nome
        profissional_campeonato.delete()
        messages.success(request, f'Profissional {profissional_nome} removido do campeonato com sucesso!')
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
    
    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def time_edit(request, pk):
    """View para editar time com redirecionamento para campeonato se especificado"""
    tenant = get_tenant_for_user(request)
    time = get_object_or_404(Time, pk=pk, tenant=tenant)
    campeonato_id = request.GET.get('campeonato')
    
    from .forms import TimeForm
    
    if request.method == 'POST':
        form = TimeForm(request.POST, request.FILES, instance=time)
        if form.is_valid():
            form.save()
            messages.success(request, f'Time {time.nome} atualizado com sucesso!')
            
            # Redirecionar para o campeonato se especificado
            if campeonato_id:
                return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
            return redirect('campeonato:time_detail', pk=time.pk)
    else:
        form = TimeForm(instance=time)
    
    context = {
        'form': form,
        'time': time,
        'campeonato_id': campeonato_id,
        'title': f'Editar {time.nome}',
    }
    return render(request, 'campeonato/time_edit.html', context)


@login_required
def profissional_edit(request, pk):
    """View para editar profissional com redirecionamento para campeonato se especificado"""
    try:
        tenant = get_tenant_for_user(request)
        profissional = get_object_or_404(Profissional, pk=pk, tenant=tenant)
        campeonato_id = request.GET.get('campeonato')
        
        from .forms import ProfissionalForm
        
        if request.method == 'POST':
            form = ProfissionalForm(request.POST, request.FILES, instance=profissional)
            if form.is_valid():
                form.save()
                messages.success(request, f'Profissional {profissional.nome} atualizado com sucesso!')
                
                # Redirecionar para o campeonato se especificado
                if campeonato_id:
                    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
                return redirect('campeonato:profissional_detail', pk=profissional.pk)
        else:
            form = ProfissionalForm(instance=profissional)
        
        context = {
            'form': form,
            'profissional': profissional,
            'campeonato_id': campeonato_id,
            'title': f'Editar {profissional.nome}',
        }
        return render(request, 'campeonato/profissional_edit.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao editar profissional: {str(e)}')
        if campeonato_id:
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
        return redirect('campeonato:profissionais_list')


@login_required
def vincular_jogador_time(request, campeonato_pk, time_campeonato_pk):
    """View para vincular um jogador a um time no campeonato"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    time_campeonato = get_object_or_404(TimeCampeonato, pk=time_campeonato_pk, campeonato=campeonato)
    
    if request.method == 'POST':
        jogador_existente = request.POST.get('jogador_existente')
        
        if jogador_existente:
            # Vincular jogador existente
            jogador = get_object_or_404(Jogador, pk=jogador_existente, tenant=tenant)
            
            # Verificar se já não está vinculado
            if not JogadorTimeCampeonato.objects.filter(time_campeonato=time_campeonato, jogador=jogador, ativo=True).exists():
                JogadorTimeCampeonato.objects.create(
                    time_campeonato=time_campeonato,
                    jogador=jogador,
                    data_entrada=timezone.now().date(),
                    ativo=True
                )
                messages.success(request, f'Jogador {jogador.nome} vinculado com sucesso!')
            else:
                messages.error(request, f'Jogador {jogador.nome} já está vinculado ao time.')
        else:
            # Criar novo jogador
            nome = request.POST.get('nome')
            data_nascimento = request.POST.get('data_nascimento')
            cidade = request.POST.get('cidade')
            telefone = request.POST.get('telefone', '')
            logradouro = request.POST.get('logradouro', '')
            bairro = request.POST.get('bairro', '')
            cep = request.POST.get('cep', '')
            complemento = request.POST.get('complemento', '')
            titulo_eleitor = request.POST.get('titulo_eleitor', '')
            zona_eleitoral = request.POST.get('zona_eleitoral', '')
            secao_eleitoral = request.POST.get('secao_eleitoral', '')
            
            if nome and data_nascimento and cidade:
                jogador = Jogador.objects.create(
                    nome=nome,
                    data_nascimento=data_nascimento,
                    cidade=cidade,
                    telefone=telefone,
                    logradouro=logradouro,
                    bairro=bairro,
                    cep=cep,
                    complemento=complemento,
                    titulo_eleitor=titulo_eleitor,
                    zona_eleitoral=zona_eleitoral,
                    secao_eleitoral=secao_eleitoral,
                    tenant=tenant
                )
                
                JogadorTimeCampeonato.objects.create(
                    time_campeonato=time_campeonato,
                    jogador=jogador,
                    data_entrada=timezone.now().date(),
                    ativo=True
                )
                messages.success(request, f'Jogador {jogador.nome} criado e vinculado com sucesso!')
            else:
                messages.error(request, 'Nome, data de nascimento e cidade são obrigatórios.')
    
    return redirect('campeonato:jogadores_time', campeonato_pk=campeonato_pk, time_campeonato_pk=time_campeonato_pk)


@login_required
def desvincular_jogador_time(request, campeonato_pk, vinculo_pk):
    """View para desvincular um jogador de um time"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    vinculo = get_object_or_404(JogadorTimeCampeonato, pk=vinculo_pk, time_campeonato__campeonato=campeonato)
    
    if request.method == 'POST':
        jogador_nome = vinculo.jogador.nome
        vinculo.ativo = False
        vinculo.data_saida = timezone.now().date()
        vinculo.save()
        messages.success(request, f'Jogador {jogador_nome} desvinculado com sucesso!')
        
        # Redirecionar para a view apropriada
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
    
    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def desvincular_time_campeonato(request, campeonato_pk, time_campeonato_pk):
    """View para desvincular um time do campeonato"""
    tenant = get_tenant_for_user(request)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
    time_campeonato = get_object_or_404(TimeCampeonato, pk=time_campeonato_pk, campeonato=campeonato)
    
    if request.method == 'POST':
        time_nome = time_campeonato.time.nome
        time_campeonato.delete()
        messages.success(request, f'Time {time_nome} removido do campeonato com sucesso!')
        return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
    
    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)


@login_required
def gerar_rodadas_campeonato(request, campeonato_pk):
    """Gerar rodadas para o campeonato baseado no formato"""
    from django.http import JsonResponse
    import json
    from itertools import combinations
    from datetime import date, timedelta
    
    try:
        tenant = get_tenant_for_user(request)
        campeonato = get_object_or_404(Campeonato, pk=campeonato_pk, tenant=tenant)
        
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método não permitido'})
        
        # Verificar se há times suficientes
        times_campeonato = TimeCampeonato.objects.filter(campeonato=campeonato)
        if times_campeonato.count() < 2:
            return JsonResponse({'success': False, 'error': 'É necessário ter pelo menos 2 times para gerar rodadas'})
        
        # Limpar rodadas existentes se houver
        campeonato.rodadas.all().delete()
        
        # Gerar rodadas baseado no formato
        if campeonato.tipo_formato == 'liga':
            return _gerar_rodadas_liga(campeonato, times_campeonato)
        elif campeonato.tipo_formato == 'mata_mata':
            return _gerar_rodadas_mata_mata(campeonato, times_campeonato)
        elif campeonato.tipo_formato == 'misto':
            return _gerar_rodadas_misto(campeonato, times_campeonato)
        else:
            return JsonResponse({'success': False, 'error': 'Formato de campeonato não suportado ainda'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})

def _gerar_rodadas_liga(campeonato, times_campeonato):
    """Gerar rodadas para formato Liga (pontos corridos)"""
    from datetime import date, timedelta
    from itertools import combinations
    
    times = list(times_campeonato)
    num_times = len(times)
    
    # Se número ímpar de times, adicionar um "bye" (folga)
    if num_times % 2 == 1:
        times.append(None)  # Representa folga
        num_times += 1
    
    # Algoritmo round-robin para gerar partidas
    rodadas_turno = []
    for rodada_num in range(num_times - 1):
        partidas_rodada = []
        
        # Primeira metade vs segunda metade
        for i in range(num_times // 2):
            time1 = times[i]
            time2 = times[num_times - 1 - i]
            
            # Pular se algum for None (bye/folga)
            if time1 is not None and time2 is not None:
                partidas_rodada.append((time1, time2))
        
        if partidas_rodada:  # Só adicionar se houver partidas
            rodadas_turno.append(partidas_rodada)
        
        # Rotacionar times (mantendo o primeiro fixo)
        times = [times[0]] + [times[-1]] + times[1:-1]
    
    # Criar rodadas no banco de dados
    rodada_counter = 1
    data_base = campeonato.data_inicio or date.today()
    
    # Turno (First Leg)
    for i, partidas_rodada in enumerate(rodadas_turno):
        # Nome da rodada baseado no formato internacional
        if campeonato.ida_volta:
            nome_rodada = f"Rodada {rodada_counter} - Turno"
        else:
            nome_rodada = f"Rodada {rodada_counter}"
        
        rodada = Rodada.objects.create(
            campeonato=campeonato,
            numero=rodada_counter,
            nome=nome_rodada,
            data=data_base + timedelta(weeks=i)
        )
        
        for time_mandante, time_visitante in partidas_rodada:
            Partida.objects.create(
                rodada=rodada,
                time_mandante=time_mandante,
                time_visitante=time_visitante,
                status='nao_iniciada'
            )
        
        rodada_counter += 1
    
    # Returno (Second Leg - se habilitado)
    if campeonato.ida_volta:
        for i, partidas_rodada in enumerate(rodadas_turno):
            nome_rodada = f"Rodada {rodada_counter} - Returno"
            
            rodada = Rodada.objects.create(
                campeonato=campeonato,
                numero=rodada_counter,
                nome=nome_rodada,
                data=data_base + timedelta(weeks=len(rodadas_turno) + i)
            )
            
            # Inverter mandante e visitante no returno
            for time_mandante, time_visitante in partidas_rodada:
                Partida.objects.create(
                    rodada=rodada,
                    time_mandante=time_visitante,  # Invertido
                    time_visitante=time_mandante,  # Invertido
                    status='nao_iniciada'
                )
            
            rodada_counter += 1
    
    total_rodadas = rodada_counter - 1
    total_partidas = sum(rodada.partidas.count() for rodada in campeonato.rodadas.all())
    
    message = f"{total_rodadas} rodadas geradas com sucesso com {total_partidas} partidas!"
    if campeonato.ida_volta:
        message = f"{total_rodadas} rodadas geradas (formato ida e volta) com {total_partidas} partidas!"
    
    return JsonResponse({
        'success': True, 
        'message': message,
        'total_rodadas': total_rodadas,
        'total_partidas': total_partidas
    })

def _gerar_rodadas_mata_mata(campeonato, times_campeonato):
    """Gerar rodadas para formato Mata-mata"""
    from datetime import date, timedelta
    import math
    import random
    
    times = list(times_campeonato)
    num_times = len(times)
    
    if num_times < 2:
        return JsonResponse({'success': False, 'error': 'At least 2 teams required for knockout format'})
    
    # Calcular número de fases necessárias
    num_fases = math.ceil(math.log2(num_times))
    data_base = campeonato.data_inicio or date.today()
    
    # Encontrar a próxima potência de 2
    proxima_potencia = 2 ** num_fases
    
    # Embaralhar times para sorteio
    random.shuffle(times)
    
    # Adicionar "byes" se necessário
    times_com_bye = times + [None] * (proxima_potencia - num_times)
    
    # Gerar fases do mata-mata
    rodada_counter = 1
    times_atual = times_com_bye
    
    while len([t for t in times_atual if t is not None]) > 1:
        # Determinar nome da fase
        times_restantes = len([t for t in times_atual if t is not None])
        
        if times_restantes <= 2:
            nome_fase = "Final"
        elif times_restantes <= 4:
            nome_fase = "Semifinal"
        elif times_restantes <= 8:
            nome_fase = "Quarterfinal"
        elif times_restantes <= 16:
            nome_fase = "Oitavas de Final"
        else:
            nome_fase = f"Rodada {rodada_counter}"
        
        # Criar rodada
        rodada = Rodada.objects.create(
            campeonato=campeonato,
            numero=rodada_counter,
            nome=nome_fase,
            data=data_base + timedelta(weeks=rodada_counter-1)
        )
        
        # Criar partidas desta fase
        proximos_times = []
        
        for i in range(0, len(times_atual), 2):
            time1 = times_atual[i] if i < len(times_atual) else None
            time2 = times_atual[i+1] if i+1 < len(times_atual) else None
            
            # Se um dos times é None (bye), o outro avança automaticamente
            if time1 is None and time2 is not None:
                proximos_times.append(time2)
            elif time2 is None and time1 is not None:
                proximos_times.append(time1)
            elif time1 is not None and time2 is not None:
                # Criar partida real
                Partida.objects.create(
                    rodada=rodada,
                    time_mandante=time1,
                    time_visitante=time2,
                    status='nao_iniciada'
                )
                # Por enquanto, adicionar o primeiro time como "vencedor" para próxima fase
                # Em uma implementação real, isso seria determinado após o resultado da partida
                proximos_times.append(time1)
        
        times_atual = proximos_times
        rodada_counter += 1
        
        # Segurança para evitar loop infinito
        if rodada_counter > 10:
            break
    
    total_rodadas = rodada_counter - 1
    total_partidas = sum(rodada.partidas.count() for rodada in campeonato.rodadas.all())
    
    return JsonResponse({
        'success': True, 
        'message': f"{total_rodadas} rodadas mata-mata geradas com {total_partidas} partidas!",
        'total_rodadas': total_rodadas,
        'total_partidas': total_partidas
    })

def _gerar_rodadas_misto(campeonato, times_campeonato):
    """Gerar rodadas para formato Misto (fase de grupos + mata-mata)"""
    from datetime import date, timedelta
    
    times = list(times_campeonato)
    num_times = len(times)
    num_grupos = campeonato.num_grupos or 1
    
    if num_grupos <= 0:
        return JsonResponse({'success': False, 'error': 'Número de grupos inválido.'})
    
    # Validar se o número de times é suficiente
    if num_times < num_grupos * 2:
        return JsonResponse({'success': False, 'error': f'Não há times suficientes para formar {num_grupos} grupos.'})
    
    # Dividir times em grupos
    random.shuffle(times)
    grupos = [[] for _ in range(num_grupos)]
    for i, time in enumerate(times):
        grupos[i % num_grupos].append(time)
    
    # Verificar tamanho dos grupos
    tamanho_grupo = max(len(grupo) for grupo in grupos)
    
    # Adicionar "bye" aos grupos menores se necessário
    for grupo in grupos:
        while len(grupo) < tamanho_grupo:
            if tamanho_grupo % 2 == 1:
                grupo.append(None)  # Adicionar bye
                break
    
    # Gerar rodadas de forma que cada rodada tenha partidas de todos os grupos
    rodada_counter = 1
    data_base = campeonato.data_inicio or date.today()
    total_partidas_grupos = 0
    
    # Calcular o número de rodadas necessárias para a fase de grupos
    times_com_bye = tamanho_grupo + (1 if tamanho_grupo % 2 == 1 else 0)
    num_rodadas_grupo = times_com_bye - 1
    
    # Gerar as rodadas da fase de grupos
    for rodada_num in range(num_rodadas_grupo):
        rodada, created = Rodada.objects.get_or_create(
            campeonato=campeonato,
            numero=rodada_counter,
            defaults={
                'nome': f"Rodada {rodada_counter} - Fase de Grupos",
                'data': data_base + timedelta(weeks=rodada_num)
            }
        )
        
        # Para cada grupo, gerar partidas desta rodada
        for i, grupo_times in enumerate(grupos):
            grupo_copia = list(grupo_times)  # Criar uma cópia para manipulação
            num_times_grupo = len(grupo_copia)
            
            # Adicionar "bye" se ímpar
            if num_times_grupo % 2 == 1:
                grupo_copia.append(None)
                num_times_grupo += 1
            
            # Gerar partidas desta rodada para este grupo
            for j in range(num_times_grupo // 2):
                # Ajuste para a rotação das rodadas
                pos1 = j
                pos2 = num_times_grupo - 1 - j
                
                # Aplicar rotação baseada na rodada atual
                if rodada_num > 0:
                    # Rotacionar todos exceto o primeiro
                    rotacao = rodada_num % (num_times_grupo - 1)
                    if pos1 > 0:
                        pos1 = ((pos1 - 1 + rotacao) % (num_times_grupo - 1)) + 1
                    if pos2 > 0:
                        pos2 = ((pos2 - 1 + rotacao) % (num_times_grupo - 1)) + 1
                
                time1 = grupo_copia[pos1] if pos1 < len(grupo_copia) else None
                time2 = grupo_copia[pos2] if pos2 < len(grupo_copia) else None
                
                if time1 and time2:
                    Partida.objects.create(
                        rodada=rodada,
                        time_mandante=time1,
                        time_visitante=time2,
                        status='nao_iniciada'
                    )
                    total_partidas_grupos += 1
        
        rodada_counter += 1

    # Gerar fases de mata-mata
    num_classificados = campeonato.num_classificados or 2
    total_classificados = min(num_classificados * num_grupos, num_times)  # Total de classificados de todos os grupos
    
    # Adicionar rodadas de mata-mata
    if total_classificados > 1:
        try:
            # Calcula o número de fases de mata-mata necessárias
            fases_mata_mata = math.ceil(math.log2(total_classificados))
        except ValueError:
            fases_mata_mata = 0  # Caso total_classificados seja 0 ou 1

        for fase in range(fases_mata_mata):
            # Calcula quantos times participam desta fase (começando do total e diminuindo)
            times_na_fase = 2**(fases_mata_mata - fase)

            if times_na_fase < 2: 
                break
            
            if times_na_fase <= 2: 
                nome_fase = "Final"
            elif times_na_fase <= 4: 
                nome_fase = "Semifinal"
            elif times_na_fase <= 8: 
                nome_fase = "Quartas de Final"
            else: 
                nome_fase = f"Fase de {times_na_fase} times"
            
            rodada = Rodada.objects.create(
                campeonato=campeonato,
                numero=rodada_counter,
                nome=nome_fase,
                data=data_base + timedelta(weeks=rodada_counter - 1)
            )
            
            # Criar partidas placeholder
            partidas_na_fase = times_na_fase // 2
            for i in range(partidas_na_fase):
                Partida.objects.create(
                    rodada=rodada,
                    status='nao_iniciada',
                    observacoes=f"A definir - aguardando classificação dos grupos"
                )
            
            rodada_counter += 1
    
    total_rodadas = rodada_counter - 1
    message = f"Fase de grupos e mata-mata gerados com sucesso! ({total_partidas_grupos} partidas na fase de grupos)"
    
    return JsonResponse({
        'success': True, 
        'message': message,
        'total_rodadas': total_rodadas,
        'total_partidas': total_partidas_grupos
    })

@login_required  
def editar_rodada(request, rodada_pk):
    """Editar informações de uma rodada"""
    try:
        tenant = get_tenant_for_user(request)
        rodada = get_object_or_404(Rodada, pk=rodada_pk, campeonato__tenant=tenant)
        campeonato_id = request.GET.get('campeonato')
        
        # Por agora, redirecionar de volta
        if campeonato_id:
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_id)
        return redirect('campeonato:dashboard')
        
    except Exception as e:
        messages.error(request, f'Erro ao editar rodada: {str(e)}')
        return redirect('campeonato:dashboard')

@login_required
def gerenciar_partida(request, partida_pk):
    """Gerenciar uma partida específica - View dedicada com interface completa"""
    from django.utils import timezone
    from .models import Gol, Cartao, JogadorTimeCampeonato
    import traceback
    
    try:
        tenant = get_tenant_for_user(request)
        partida = get_object_or_404(Partida, pk=partida_pk, rodada__campeonato__tenant=tenant)
        
        # Buscar dados relacionados
        gols = partida.gols.all().select_related('jogador__jogador', 'time__time').order_by('minuto')
        cartoes = partida.cartoes.all().select_related('jogador__jogador', 'jogador__time_campeonato__time').order_by('minuto')
        
        # Separar cartões por tipo para estatísticas
        cartoes_amarelos = cartoes.filter(tipo='AMA')
        cartoes_vermelhos = cartoes.filter(tipo='VER')
        
        # Buscar jogadores disponíveis para cada time
        jogadores_mandante = JogadorTimeCampeonato.objects.filter(
            time_campeonato=partida.time_mandante,
            ativo=True
        ).select_related('jogador')
        
        jogadores_visitante = JogadorTimeCampeonato.objects.filter(
            time_campeonato=partida.time_visitante,
            ativo=True
        ).select_related('jogador')
        
        # Processar ações POST
        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'update_info':
                partida.data_hora = request.POST.get('data_hora') or None
                partida.local = request.POST.get('local') or ''
                partida.status = request.POST.get('status', partida.status)
                partida.observacoes = request.POST.get('observacoes') or ''
                partida.save()
                messages.success(request, 'Informações da partida atualizadas com sucesso!')

            elif action == 'update_placar':
                partida.placar_mandante = int(request.POST.get('placar_mandante', 0))
                partida.placar_visitante = int(request.POST.get('placar_visitante', 0))
                partida.save()
                messages.success(request, 'Placar atualizado com sucesso!')

            elif action == 'iniciar_partida':
                partida.status = 'em_andamento'
                if not partida.data_hora:
                    partida.data_hora = timezone.now()
                partida.save()
                messages.success(request, 'Partida iniciada!')

            elif action == 'finalizar_partida':
                partida.status = 'finalizada'
                partida.save()
                messages.success(request, 'Partida finalizada!')

            elif action == 'add_gol':
                try:
                    time_campeonato = get_object_or_404(TimeCampeonato, pk=request.POST.get('time_id'))
                    jogador_tc = get_object_or_404(JogadorTimeCampeonato, pk=request.POST.get('jogador_id'))
                    gol = Gol.objects.create(
                        partida=partida,
                        jogador=jogador_tc,
                        time=time_campeonato,
                        minuto=int(request.POST.get('minuto')),
                        tipo=request.POST.get('tipo', 'NOR')
                    )
                    if time_campeonato == partida.time_mandante:
                        if gol.tipo == 'CON':
                            partida.placar_visitante += 1
                        else:
                            partida.placar_mandante += 1
                    else:
                        if gol.tipo == 'CON':
                            partida.placar_mandante += 1
                        else:
                            partida.placar_visitante += 1
                    partida.save()
                    messages.success(request, f'Gol de {jogador_tc.jogador.nome} adicionado!')
                except Exception as e:
                    messages.error(request, f'Erro ao adicionar gol: {str(e)}')

            elif action == 'add_cartao':
                try:
                    jogador_tc = get_object_or_404(JogadorTimeCampeonato, pk=request.POST.get('jogador_id'))
                    tipo_cartao = request.POST.get('tipo', 'AMA')
                    cartoes_existentes = Cartao.objects.filter(partida=partida, jogador=jogador_tc)
                    cartoes_amarelos = cartoes_existentes.filter(tipo='AMA').count()
                    cartoes_vermelhos = cartoes_existentes.filter(tipo='VER').count()
                    if tipo_cartao == 'AMA' and cartoes_amarelos >= 2:
                        messages.error(request, f'{jogador_tc.jogador.nome} já possui 2 cartões amarelos!')
                    elif tipo_cartao == 'VER' and cartoes_vermelhos >= 1:
                        messages.error(request, f'{jogador_tc.jogador.nome} já possui cartão vermelho!')
                    else:
                        Cartao.objects.create(
                            partida=partida,
                            jogador=jogador_tc,
                            tipo=tipo_cartao,
                            minuto=int(request.POST.get('minuto')),
                            motivo=request.POST.get('motivo', '')
                        )
                        tipo_display = 'Amarelo' if tipo_cartao == 'AMA' else 'Vermelho'
                        messages.success(request, f'Cartão {tipo_display} para {jogador_tc.jogador.nome} adicionado!')
                except Exception as e:
                    messages.error(request, f'Erro ao adicionar cartão: {str(e)}')

            elif action == 'delete_gol':
                try:
                    gol = get_object_or_404(Gol, pk=request.POST.get('gol_id'), partida=partida)
                    jogador_nome = gol.jogador.jogador.nome
                    if gol.time == partida.time_mandante:
                        if gol.tipo == 'CON':
                            partida.placar_visitante -= 1
                        else:
                            partida.placar_mandante -= 1
                    else:
                        if gol.tipo == 'CON':
                            partida.placar_mandante -= 1
                        else:
                            partida.placar_visitante -= 1
                    partida.save()
                    gol.delete()
                    messages.success(request, f'Gol de {jogador_nome} removido!')
                except Exception as e:
                    messages.error(request, f'Erro ao remover gol: {str(e)}')

            elif action == 'delete_cartao':
                try:
                    cartao = get_object_or_404(Cartao, pk=request.POST.get('cartao_id'), partida=partida)
                    jogador_nome = cartao.jogador.jogador.nome
                    cartao.delete()
                    messages.success(request, f'Cartão de {jogador_nome} removido!')
                except Exception as e:
                    messages.error(request, f'Erro ao remover cartão: {str(e)}')

            elif action == 'update_profissionais':
                from .models import ProfissionalPartida, ProfissionalCampeonato
                funcoes = [
                    ('arbitro', 'ARB'),
                    ('bandeira1', 'BAN'),
                    ('bandeira2', 'BAN'),
                    ('mesario', 'MES'),
                    ('quarto_arbitro', 'QAR'),
                ]
                ProfissionalPartida.objects.filter(partida=partida).delete()
                usados = set()
                for nome, funcao in funcoes:
                    prof_id = request.POST.get(nome)
                    if prof_id:
                        if prof_id in usados:
                            continue
                        usados.add(prof_id)
                        prof_camp = ProfissionalCampeonato.objects.filter(id=prof_id, campeonato=partida.rodada.campeonato).first()
                        if prof_camp:
                            ProfissionalPartida.objects.create(
                                profissional_campeonato=prof_camp,
                                partida=partida,
                                funcao=funcao
                            )
                messages.success(request, 'Profissionais da partida atualizados!')

            # Redirect para evitar resubmissão
            return redirect('campeonato:gerenciar_partida', partida_pk=partida_pk)
        
        # Profissionais disponíveis: todos do campeonato
        from .models import ProfissionalCampeonato, ProfissionalPartida
        profissionais_disponiveis = ProfissionalCampeonato.objects.filter(campeonato=partida.rodada.campeonato)

        # Profissionais já vinculados à partida, por função
        profissionais_partida = {
            'arbitro': None,
            'bandeira1': None,
            'bandeira2': None,
            'mesario': None,
            'quarto_arbitro': None,
        }
        for prof in ProfissionalPartida.objects.filter(partida=partida):
            if prof.funcao == 'ARB':
                profissionais_partida['arbitro'] = prof.profissional_campeonato
            elif prof.funcao == 'BAN':
                if not profissionais_partida['bandeira1']:
                    profissionais_partida['bandeira1'] = prof.profissional_campeonato
                else:
                    profissionais_partida['bandeira2'] = prof.profissional_campeonato
            elif prof.funcao == 'MES':
                profissionais_partida['mesario'] = prof.profissional_campeonato
            elif prof.funcao == 'QAR':
                profissionais_partida['quarto_arbitro'] = prof.profissional_campeonato

        context = {
            'partida': partida,
            'gols': gols,
            'cartoes': cartoes,
            'cartoes_amarelos': cartoes_amarelos,
            'cartoes_vermelhos': cartoes_vermelhos,
            'jogadores_mandante': jogadores_mandante,
            'jogadores_visitante': jogadores_visitante,
            'profissionais_disponiveis': profissionais_disponiveis,
            'profissionais_partida': profissionais_partida,
            'title': f'Gerenciar Partida: {partida.time_mandante.time.nome} vs {partida.time_visitante.time.nome}'
        }

        return render(request, 'campeonato/partida_gerenciar.html', context)
        
    except Exception as e:
        print(f"DEBUG: Erro em gerenciar_partida: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Erro ao gerenciar partida: {str(e)}')
        return redirect('campeonato:dashboard')

# Views API para modais de edição

@login_required
def rodada_detail_api(request, rodada_pk):
    """API para obter detalhes de uma rodada"""
    from django.http import JsonResponse
    
    try:
        tenant = get_tenant_for_user(request)
        rodada = get_object_or_404(Rodada, pk=rodada_pk, campeonato__tenant=tenant)
        
        data = {
            'success': True,
            'rodada': {
                'id': rodada.id,
                'numero': rodada.numero,
                'nome': rodada.nome,
                'data': rodada.data.isoformat() if rodada.data else None,
                'observacoes': rodada.observacoes,
                'nome_exibicao': rodada.get_nome_exibicao(),
                'partidas_count': rodada.partidas.count()
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def rodada_update_api(request, rodada_pk):
    """API para atualizar uma rodada"""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        tenant = get_tenant_for_user(request)
        rodada = get_object_or_404(Rodada, pk=rodada_pk, campeonato__tenant=tenant)
        
        # Atualizar campos
        if 'nome' in request.POST:
            rodada.nome = request.POST.get('nome', '').strip() or None
        
        if 'data' in request.POST:
            data_str = request.POST.get('data')
            if data_str:
                from datetime import datetime
                rodada.data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        if 'observacoes' in request.POST:
            rodada.observacoes = request.POST.get('observacoes', '').strip() or None
        
        rodada.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Rodada {rodada.get_nome_exibicao()} atualizada com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def partida_detail_api(request, partida_pk):
    """API para obter detalhes de uma partida"""
    from django.http import JsonResponse
    
    try:
        tenant = get_tenant_for_user(request)
        partida = get_object_or_404(Partida, pk=partida_pk, rodada__campeonato__tenant=tenant)
        
        data = {
            'success': True,
            'partida': {
                'id': partida.id,
                'data_hora': partida.data_hora.isoformat() if partida.data_hora else None,
                'local': partida.local,
                'status': partida.status,
                'placar_mandante': partida.placar_mandante,
                'placar_visitante': partida.placar_visitante,
                'observacoes': partida.observacoes,
                'time_mandante': {
                    'id': partida.time_mandante.id if partida.time_mandante else None,
                    'nome': partida.time_mandante.time.nome if partida.time_mandante else None,
                    'escudo': partida.time_mandante.time.escudo.url if partida.time_mandante and partida.time_mandante.time.escudo else None
                } if partida.time_mandante else None,
                'time_visitante': {
                    'id': partida.time_visitante.id if partida.time_visitante else None,
                    'nome': partida.time_visitante.time.nome if partida.time_visitante else None,
                    'escudo': partida.time_visitante.time.escudo.url if partida.time_visitante and partida.time_visitante.time.escudo else None
                } if partida.time_visitante else None
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def partida_update_api(request, partida_pk):
    """API para atualizar uma partida"""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        tenant = get_tenant_for_user(request)
        partida = get_object_or_404(Partida, pk=partida_pk, rodada__campeonato__tenant=tenant)
        
        # Atualizar campos
        if 'data_hora' in request.POST:
            data_hora_str = request.POST.get('data_hora')
            if data_hora_str:
                from datetime import datetime
                partida.data_hora = datetime.fromisoformat(data_hora_str)
            else:
                partida.data_hora = None
        
        if 'local' in request.POST:
            partida.local = request.POST.get('local', '').strip()
        
        if 'status' in request.POST:
            status = request.POST.get('status')
            if status in ['nao_iniciada', 'em_andamento', 'finalizada']:
                partida.status = status
        
        if 'placar_mandante' in request.POST:
            try:
                partida.placar_mandante = int(request.POST.get('placar_mandante', 0))
            except (ValueError, TypeError):
                partida.placar_mandante = 0
        
        if 'placar_visitante' in request.POST:
            try:
                partida.placar_visitante = int(request.POST.get('placar_visitante', 0))
            except (ValueError, TypeError):
                partida.placar_visitante = 0
        
        if 'observacoes' in request.POST:
            partida.observacoes = request.POST.get('observacoes', '').strip() or None
        
        # Marcar como encerrada se finalizada e tem placar
        if partida.status == 'finalizada':
            partida.encerrada = True
        else:
            partida.encerrada = False
        
        partida.save()
        
        # Formar mensagem com resultado se finalizada
        if partida.status == 'finalizada':
            time_mandante_nome = partida.time_mandante.time.nome if partida.time_mandante else "Team A"
            time_visitante_nome = partida.time_visitante.time.nome if partida.time_visitante else "Team B"
            message = f'Match updated! {time_mandante_nome} {partida.placar_mandante} x {partida.placar_visitante} {time_visitante_nome}'
        else:
            message = 'Match updated successfully!'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Funções auxiliares para cálculo de estatísticas
def calcular_classificacao(campeonato):
    """Calcula a classificação geral do campeonato"""
    from django.db.models import Sum, Count, Q
    
    times_campeonato = campeonato.times.all()
    classificacao = []
    
    for time_campeonato in times_campeonato:
        # Buscar partidas do time
        partidas_mandante = Partida.objects.filter(
            time_mandante=time_campeonato,
            status='finalizada'
        )
        partidas_visitante = Partida.objects.filter(
            time_visitante=time_campeonato,
            status='finalizada'
        )
        
        # Inicializar estatísticas
        jogos = partidas_mandante.count() + partidas_visitante.count()
        vitorias = empates = derrotas = 0
        gols_pro = gols_contra = 0
        
        # Calcular como mandante
        for partida in partidas_mandante:
            gols_pro += partida.placar_mandante
            gols_contra += partida.placar_visitante
            
            if partida.placar_mandante > partida.placar_visitante:
                vitorias += 1
            elif partida.placar_mandante == partida.placar_visitante:
                empates += 1
            else:
                derrotas += 1
        
        # Calcular como visitante
        for partida in partidas_visitante:
            gols_pro += partida.placar_visitante
            gols_contra += partida.placar_mandante
            
            if partida.placar_visitante > partida.placar_mandante:
                vitorias += 1
            elif partida.placar_visitante == partida.placar_mandante:
                empates += 1
            else:
                derrotas += 1
        
        # Calcular pontos e saldo
        pontos = (vitorias * 3) + empates
        saldo_gols = gols_pro - gols_contra
        
        classificacao.append({
            'time': time_campeonato.time,
            'jogos': jogos,
            'vitorias': vitorias,
            'empates': empates,
            'derrotas': derrotas,
            'gols_pro': gols_pro,
            'gols_contra': gols_contra,
            'saldo_gols': saldo_gols,
            'pontos': pontos,
            'grupo': 'A'  # Default, pode ser expandido
        })
    
    # Ordenar por pontos, saldo de gols, gols pró
    classificacao.sort(key=lambda x: (-x['pontos'], -x['saldo_gols'], -x['gols_pro']))
    return classificacao


def calcular_artilharia(campeonato):
    """Calcula a artilharia do campeonato"""
    from django.db.models import Count
    
    artilheiros = []
    gols = Gol.objects.filter(
        partida__rodada__campeonato=campeonato
    ).values(
        'jogador__jogador__nome',
        'jogador__jogador__foto',
        'time__time__nome'
    ).annotate(
        gols=Count('id')
    ).order_by('-gols')
    
    for gol in gols:
        artilheiros.append({
            'jogador': {
                'nome': gol['jogador__jogador__nome'],
                'foto': gol['jogador__jogador__foto']
            },
            'time': {'nome': gol['time__time__nome']},
            'gols': gol['gols']
        })
    
    return artilheiros


def calcular_assistencias(campeonato):
    """Calcula assistências - implementação futura"""
    return []


def calcular_cartoes_amarelos(campeonato):
    """Calcula cartões amarelos"""
    from django.db.models import Count
    
    cartoes = Cartao.objects.filter(
        partida__rodada__campeonato=campeonato,
        tipo='AMA'
    ).values(
        'jogador__jogador__nome',
        'jogador__time_campeonato__time__nome'
    ).annotate(
        cartoes=Count('id')
    ).order_by('-cartoes')[:10]
    
    resultado = []
    for cartao in cartoes:
        resultado.append({
            'jogador': {'nome': cartao['jogador__jogador__nome']},
            'time': {'nome': cartao['jogador__time_campeonato__time__nome']},
            'cartoes': cartao['cartoes']
        })
    
    return resultado


def calcular_cartoes_vermelhos(campeonato):
    """Calcula cartões vermelhos"""
    from django.db.models import Count
    
    cartoes = Cartao.objects.filter(
        partida__rodada__campeonato=campeonato,
        tipo='VER'
    ).values(
        'jogador__jogador__nome',
        'jogador__time_campeonato__time__nome'
    ).annotate(
        cartoes=Count('id')
    ).order_by('-cartoes')[:10]
    
    resultado = []
    for cartao in cartoes:
        resultado.append({
            'jogador': {'nome': cartao['jogador__jogador__nome']},
            'time': {'nome': cartao['jogador__time_campeonato__time__nome']},
            'cartoes': cartao['cartoes']
        })
    
    return resultado


def calcular_classificacao_por_grupos(campeonato):
    """Calcula classificação por grupos para campeonatos mistos"""
    if campeonato.tipo_formato != 'misto' or not campeonato.num_grupos:
        return []
    
    # Buscar todos os times do campeonato
    times_campeonato = list(TimeCampeonato.objects.filter(
        campeonato=campeonato
    ).select_related('time'))
    
    if not times_campeonato:
        return []
    
    num_grupos = campeonato.num_grupos
    classificacao_grupos = []
    
    # Dividir times em grupos (simulando a mesma lógica da geração de rodadas)
    grupos = [[] for _ in range(num_grupos)]
    for i, time in enumerate(times_campeonato):
        grupos[i % num_grupos].append(time)
    
    # Para cada grupo, calcular classificação
    for grupo_idx, times_grupo in enumerate(grupos):
        if not times_grupo:  # Pular grupos vazios
            continue
            
        letra_grupo = chr(ord('A') + grupo_idx)
        classificacao_grupo = []
        
        for time_campeonato in times_grupo:
            # Buscar partidas do time apenas contra outros times do mesmo grupo
            times_mesmo_grupo_ids = [tc.id for tc in times_grupo]
            
            partidas_casa = Partida.objects.filter(
                rodada__campeonato=campeonato,
                time_mandante=time_campeonato,
                time_visitante__id__in=times_mesmo_grupo_ids,
                status='finalizada'
            )
            
            partidas_fora = Partida.objects.filter(
                rodada__campeonato=campeonato,
                time_visitante=time_campeonato,
                time_mandante__id__in=times_mesmo_grupo_ids,
                status='finalizada'
            )
            
            # Calcular estatísticas
            vitorias = 0
            empates = 0
            derrotas = 0
            gols_pro = 0
            gols_contra = 0
            
            # Partidas em casa
            for partida in partidas_casa:
                gols_pro += partida.placar_mandante or 0
                gols_contra += partida.placar_visitante or 0
                
                if (partida.placar_mandante or 0) > (partida.placar_visitante or 0):
                    vitorias += 1
                elif (partida.placar_mandante or 0) < (partida.placar_visitante or 0):
                    derrotas += 1
                else:
                    empates += 1
            
            # Partidas fora de casa
            for partida in partidas_fora:
                gols_pro += partida.placar_visitante or 0
                gols_contra += partida.placar_mandante or 0
                
                if (partida.placar_visitante or 0) > (partida.placar_mandante or 0):
                    vitorias += 1
                elif (partida.placar_visitante or 0) < (partida.placar_mandante or 0):
                    derrotas += 1
                else:
                    empates += 1
            
            jogos = vitorias + empates + derrotas
            pontos = vitorias * 3 + empates
            saldo_gols = gols_pro - gols_contra
            
            classificacao_grupo.append({
                'time': time_campeonato.time,
                'time_campeonato': time_campeonato,
                'grupo': letra_grupo,
                'jogos': jogos,
                'vitorias': vitorias,
                'empates': empates,
                'derrotas': derrotas,
                'gols_pro': gols_pro,
                'gols_contra': gols_contra,
                'saldo_gols': saldo_gols,
                'pontos': pontos,
            })
        
        # Ordenar grupo por: pontos desc, saldo de gols desc, gols pró desc
        classificacao_grupo.sort(
            key=lambda x: (-x['pontos'], -x['saldo_gols'], -x['gols_pro'])
        )
        
        # Adicionar à lista de grupos
        classificacao_grupos.append({
            'numero': letra_grupo,
            'letra': letra_grupo,
            'times': classificacao_grupo,
            'classificados': campeonato.num_classificados or 2
        })
    
    return classificacao_grupos

def editar_time_campeonato(request, campeonato_pk, time_campeonato_pk):
    from django.shortcuts import get_object_or_404, redirect
    from .models import TimeCampeonato, Campeonato
    from .forms import TimeCampeonatoEditForm
    time_campeonato = get_object_or_404(TimeCampeonato, pk=time_campeonato_pk, campeonato_id=campeonato_pk)
    campeonato = get_object_or_404(Campeonato, pk=campeonato_pk)
    if request.method == 'POST':
        form = TimeCampeonatoEditForm(request.POST, instance=time_campeonato)
        if form.is_valid():
            form.save()
            return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)
    else:
        form = TimeCampeonatoEditForm(instance=time_campeonato)
    return redirect('campeonato:campeonato_gerenciar', pk=campeonato_pk)

def noticias_midia(request, campeonato_pk):
    from .models import Campeonato
    campeonato = Campeonato.objects.get(pk=campeonato_pk)
    from .forms import NoticiaForm, ImagemNoticiaForm, MidiaImagemForm, PatrocinioForm
    from .models import Noticia, ImagemNoticia, MidiaImagem, Patrocinio
    # Exclusão via POST (novo padrão)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_noticia':
            noticia_id = request.POST.get('noticia_id')
            Noticia.objects.filter(id=noticia_id, campeonato=campeonato).delete()
            return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
        elif action == 'delete_imagem_noticia':
            imagem_id = request.POST.get('imagem_id')
            ImagemNoticia.objects.filter(id=imagem_id, noticia__campeonato=campeonato).delete()
            return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
        elif action == 'delete_midia':
            midia_id = request.POST.get('midia_id')
            MidiaImagem.objects.filter(id=midia_id, campeonato=campeonato).delete()
            return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
        elif action == 'delete_patrocinio':
            patrocinio_id = request.POST.get('patrocinio_id')
            Patrocinio.objects.filter(id=patrocinio_id, campeonato=campeonato).delete()
            return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
    noticia_form = NoticiaForm()
    midia_form = MidiaImagemForm()
    patrocinio_form = PatrocinioForm()
    imagens_form = ImagemNoticiaForm()
    noticias = Noticia.objects.filter(campeonato=campeonato).order_by('-ultima_atualizacao')[:10]
    midias = MidiaImagem.objects.filter(campeonato=campeonato).order_by('-data_upload')[:10]
    patrocinios = Patrocinio.objects.filter(campeonato=campeonato).order_by('-data_upload')[:10]
    if request.method == 'POST':
        if 'titulo' in request.POST:
            noticia_form = NoticiaForm(request.POST)
            if noticia_form.is_valid():
                noticia = noticia_form.save(commit=False)
                noticia.campeonato = campeonato
                noticia.save()
                for img in request.FILES.getlist('imagens'):
                    ImagemNoticia.objects.create(noticia=noticia, imagem=img)
                return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
        elif 'midia_imagens' in request.FILES or 'patrocinios' in request.FILES:
            for img in request.FILES.getlist('midia_imagens'):
                MidiaImagem.objects.create(imagem=img, campeonato=campeonato)
            for img in request.FILES.getlist('patrocinios'):
                Patrocinio.objects.create(imagem=img, campeonato=campeonato)
            return redirect('campeonato:noticias_midia', campeonato_pk=campeonato_pk)
    context = {
        'campeonato': campeonato,
        'noticia_form': noticia_form,
        'midia_form': midia_form,
        'patrocinio_form': patrocinio_form,
        'imagens_form': imagens_form,
        'noticias': noticias,
        'midias': midias,
        'patrocinios': patrocinios,
    }
    return render(request, 'campeonato/noticias_midia.html', context)
