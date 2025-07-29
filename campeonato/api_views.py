from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    Time, Jogador, Profissional, Campeonato, TimeCampeonato,
    JogadorTimeCampeonato, ProfissionalCampeonato, Rodada,
    Partida, ProfissionalPartida, Gol, Cartao, Despesa
)
from .serializers import (
    TimeSerializer, JogadorSerializer, ProfissionalSerializer,
    CampeonatoSerializer, TimeCampeonatoSerializer,
    JogadorTimeCampeonatoSerializer, ProfissionalCampeonatoSerializer,
    RodadaSerializer, PartidaSerializer, GolSerializer,
    CartaoSerializer, ProfissionalPartidaSerializer, DespesaSerializer,
    EstatisticasTimeSerializer, ArtilheiroSerializer, DashboardStatsSerializer
)
from adminpanel.models import Tenant


class TenantFilteredViewSet(viewsets.ModelViewSet):
    """Base ViewSet que filtra por tenant automaticamente"""
    permission_classes = []  # Temporariamente removido para desenvolvimento

    def get_tenant(self):
        from adminpanel.models import Tenant
        try:
            # Se for superuser e há tenant_id na sessão
            if self.request.user and self.request.user.is_authenticated and self.request.user.is_superuser and self.request.session.get('tenant_id'):
                tenant_id = self.request.session.get('tenant_id')
                return Tenant.objects.get(id=tenant_id)
            # Senão, buscar tenant pelo usuário autenticado
            elif self.request.user and self.request.user.is_authenticated:
                return Tenant.objects.get(usuario=self.request.user)
            # Senão, tenta pela sessão (para chamadas AJAX de usuários logados no painel)
            elif 'tenant_id' in self.request.session:
                return Tenant.objects.get(pk=self.request.session['tenant_id'])
        except (Tenant.DoesNotExist, KeyError, ValueError):
            pass
        return None

    def get_queryset(self):
        tenant = self.get_tenant()
        if tenant and hasattr(self.queryset.model, 'tenant'):
            return self.queryset.filter(tenant=tenant).order_by('id')
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        if tenant and hasattr(serializer.Meta.model, 'tenant'):
            serializer.save(tenant=tenant)
        else:
            serializer.save()


class TimeViewSet(TenantFilteredViewSet):
    queryset = Time.objects.all().order_by('id')
    serializer_class = TimeSerializer

    @action(detail=True, methods=['get'])
    def jogadores(self, request, pk=None):
        """Retorna jogadores do time em campeonatos ativos"""
        time = self.get_object()
        vinculos_ativos = JogadorTimeCampeonato.objects.filter(
            time_campeonato__time=time,
            ativo=True
        )
        serializer = JogadorTimeCampeonatoSerializer(vinculos_ativos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Retorna estatísticas do time em um campeonato específico"""
        time = self.get_object()
        campeonato_id = request.query_params.get('campeonato_id')

        if not campeonato_id:
            return Response(
                {'error': 'campeonato_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            time_campeonato = TimeCampeonato.objects.get(
                time=time,
                campeonato_id=campeonato_id
            )

            # Calcular estatísticas
            partidas_mandante = Partida.objects.filter(
                time_mandante=time_campeonato,
                encerrada=True
            )
            partidas_visitante = Partida.objects.filter(
                time_visitante=time_campeonato,
                encerrada=True
            )

            # Contadores
            total_jogos = partidas_mandante.count() + partidas_visitante.count()
            vitorias = 0
            empates = 0
            derrotas = 0
            gols_pro = 0
            gols_contra = 0

            # Processar partidas como mandante
            for partida in partidas_mandante:
                gols_pro += partida.placar_mandante
                gols_contra += partida.placar_visitante

                if partida.placar_mandante > partida.placar_visitante:
                    vitorias += 1
                elif partida.placar_mandante == partida.placar_visitante:
                    empates += 1
                else:
                    derrotas += 1

            # Processar partidas como visitante
            for partida in partidas_visitante:
                gols_pro += partida.placar_visitante
                gols_contra += partida.placar_mandante

                if partida.placar_visitante > partida.placar_mandante:
                    vitorias += 1
                elif partida.placar_visitante == partida.placar_mandante:
                    empates += 1
                else:
                    derrotas += 1

            pontos = (vitorias * 3) + empates
            aproveitamento = (pontos / (total_jogos * 3) * 100) if total_jogos > 0 else 0

            stats = {
                'time_id': time.id,
                'time_nome': time.nome,
                'jogos': total_jogos,
                'vitorias': vitorias,
                'empates': empates,
                'derrotas': derrotas,
                'gols_pro': gols_pro,
                'gols_contra': gols_contra,
                'saldo_gols': gols_pro - gols_contra,
                'pontos': pontos,
                'aproveitamento': round(aproveitamento, 2)
            }

            serializer = EstatisticasTimeSerializer(stats)
            return Response(serializer.data)

        except TimeCampeonato.DoesNotExist:
            return Response(
                {'error': 'Time não participa deste campeonato'},
                status=status.HTTP_404_NOT_FOUND
            )


class JogadorViewSet(TenantFilteredViewSet):
    queryset = Jogador.objects.all().order_by('id')
    serializer_class = JogadorSerializer

    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Retorna estatísticas do jogador"""
        jogador = self.get_object()

        # Buscar todos os gols do jogador
        gols = Gol.objects.filter(jogador__jogador=jogador)

        # Buscar todos os cartões do jogador
        cartoes = Cartao.objects.filter(jogador__jogador=jogador)

        stats = {
            'total_gols': gols.count(),
            'gols_normais': gols.filter(tipo='NOR').count(),
            'gols_penalti': gols.filter(tipo='PEN').count(),
            'gols_contra': gols.filter(tipo='CON').count(),
            'total_cartoes': cartoes.count(),
            'cartoes_amarelos': cartoes.filter(tipo='AMA').count(),
            'cartoes_vermelhos': cartoes.filter(tipo='VER').count(),
            'times_historico': [
                {
                    'time_nome': vinculo.time_campeonato.time.nome,
                    'campeonato_nome': vinculo.time_campeonato.campeonato.nome,
                    'data_entrada': vinculo.data_entrada,
                    'data_saida': vinculo.data_saida,
                    'ativo': vinculo.ativo
                }
                for vinculo in jogador.historico.all().order_by('-data_entrada')
            ]
        }

        return Response(stats)


class ProfissionalViewSet(TenantFilteredViewSet):
    queryset = Profissional.objects.all().order_by('id')
    serializer_class = ProfissionalSerializer

    @action(detail=True, methods=['get'])
    def partidas(self, request, pk=None):
        """Retorna partidas em que o profissional atuou"""
        profissional = self.get_object()

        profissional_partidas = ProfissionalPartida.objects.filter(
            profissional_campeonato__profissional=profissional
        ).select_related('partida')

        serializer = ProfissionalPartidaSerializer(profissional_partidas, many=True)
        return Response(serializer.data)


class CampeonatoViewSet(TenantFilteredViewSet):
    queryset = Campeonato.objects.all().order_by('id')
    serializer_class = CampeonatoSerializer

    @action(detail=True, methods=['get'])
    def times(self, request, pk=None):
        """Retorna times do campeonato"""
        campeonato = self.get_object()
        times_campeonato = TimeCampeonato.objects.filter(campeonato=campeonato)
        serializer = TimeCampeonatoSerializer(times_campeonato, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tabela(self, request, pk=None):
        """Retorna tabela de classificação do campeonato"""
        campeonato = self.get_object()
        times_campeonato = TimeCampeonato.objects.filter(campeonato=campeonato)

        estatisticas = []

        for time_campeonato in times_campeonato:
            # Buscar partidas do time
            partidas_mandante = Partida.objects.filter(
                time_mandante=time_campeonato,
                encerrada=True
            )
            partidas_visitante = Partida.objects.filter(
                time_visitante=time_campeonato,
                encerrada=True
            )

            # Calcular estatísticas
            vitorias = empates = derrotas = 0
            gols_pro = gols_contra = 0

            # Como mandante
            for partida in partidas_mandante:
                gols_pro += partida.placar_mandante
                gols_contra += partida.placar_visitante

                if partida.placar_mandante > partida.placar_visitante:
                    vitorias += 1
                elif partida.placar_mandante == partida.placar_visitante:
                    empates += 1
                else:
                    derrotas += 1

            # Como visitante
            for partida in partidas_visitante:
                gols_pro += partida.placar_visitante
                gols_contra += partida.placar_mandante

                if partida.placar_visitante > partida.placar_mandante:
                    vitorias += 1
                elif partida.placar_visitante == partida.placar_mandante:
                    empates += 1
                else:
                    derrotas += 1

            total_jogos = vitorias + empates + derrotas
            pontos = (vitorias * 3) + empates
            aproveitamento = (pontos / (total_jogos * 3) * 100) if total_jogos > 0 else 0

            estatisticas.append({
                'time_id': time_campeonato.time.id,
                'time_nome': time_campeonato.time.nome,
                'escudo_url': time_campeonato.time.escudo.url if time_campeonato.time.escudo else None,
                'jogos': total_jogos,
                'vitorias': vitorias,
                'empates': empates,
                'derrotas': derrotas,
                'gols_pro': gols_pro,
                'gols_contra': gols_contra,
                'saldo_gols': gols_pro - gols_contra,
                'pontos': pontos,
                'aproveitamento': round(aproveitamento, 2)
            })

        # Ordenar por pontos, depois por saldo de gols, depois por gols pró
        estatisticas.sort(
            key=lambda x: (x['pontos'], x['saldo_gols'], x['gols_pro']),
            reverse=True
        )

        # Adicionar posição
        for i, stats in enumerate(estatisticas):
            stats['posicao'] = i + 1

        return Response(estatisticas)

    @action(detail=True, methods=['get'])
    def artilharia(self, request, pk=None):
        """Retorna artilharia do campeonato"""
        campeonato = self.get_object()

        # Buscar gols do campeonato
        gols = Gol.objects.filter(
            partida__rodada__campeonato=campeonato
        ).values(
            'jogador__jogador__id',
            'jogador__jogador__nome',
            'jogador__time_campeonato__time__nome'
        ).annotate(
            total_gols=Count('id'),
            gols_normais=Count(Case(When(tipo='NOR', then=1), output_field=IntegerField())),
            gols_penalti=Count(Case(When(tipo='PEN', then=1), output_field=IntegerField())),
            gols_contra=Count(Case(When(tipo='CON', then=1), output_field=IntegerField()))
        ).order_by('-total_gols', 'jogador__jogador__nome')

        artilheiros = []
        for gol_data in gols:
            artilheiros.append({
                'jogador_id': gol_data['jogador__jogador__id'],
                'jogador_nome': gol_data['jogador__jogador__nome'],
                'time_nome': gol_data['jogador__time_campeonato__time__nome'],
                'total_gols': gol_data['total_gols'],
                'gols_normais': gol_data['gols_normais'],
                'gols_penalti': gol_data['gols_penalti'],
                'gols_contra': gol_data['gols_contra']
            })

        # Adicionar posição
        for i, artilheiro in enumerate(artilheiros):
            artilheiro['posicao'] = i + 1

        return Response(artilheiros)

    @action(detail=True, methods=['post'])
    def vincular_time(self, request, pk=None):
        """Vincula um time ao campeonato"""
        campeonato = self.get_object()
        time_id = request.data.get('time_id')

        if not time_id:
            return Response(
                {'error': 'time_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = self.get_tenant()
        try:
            time = Time.objects.get(id=time_id, tenant=tenant)
        except Time.DoesNotExist:
            return Response(
                {'error': 'Time não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar se já está vinculado
        if TimeCampeonato.objects.filter(time=time, campeonato=campeonato).exists():
            return Response(
                {'error': 'Time já está vinculado a este campeonato'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Criar vinculação
        time_campeonato = TimeCampeonato.objects.create(
            time=time,
            campeonato=campeonato,
            localizacao=request.data.get('localizacao', ''),
            campo_estadio=request.data.get('campo_estadio', ''),
            presidente=request.data.get('presidente', '')
        )

        serializer = TimeCampeonatoSerializer(time_campeonato)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='vincular_profissional')
    def vincular_profissional(self, request, pk=None):
        """Vincula um profissional ao campeonato"""
        campeonato = self.get_object()
        profissional_id = request.data.get('profissional_id')
        funcao_principal = request.data.get('funcao_principal', 'OUT')  # Default para 'OUT' se não especificado
        
        if not profissional_id:
            return Response({'error': 'profissional_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        tenant = self.get_tenant()
        try:
            profissional = Profissional.objects.get(id=profissional_id, tenant=tenant)
        except Profissional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se já está vinculado
        if ProfissionalCampeonato.objects.filter(profissional=profissional, campeonato=campeonato).exists():
            return Response({'error': 'Profissional já está vinculado a este campeonato'}, status=status.HTTP_400_BAD_REQUEST)
          # Criar vinculação com função
        vinculo = ProfissionalCampeonato.objects.create(
            profissional=profissional,
            campeonato=campeonato,
            funcao_principal=funcao_principal
        )
        serializer = ProfissionalCampeonatoSerializer(vinculo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='desvincular_profissional')
    def desvincular_profissional(self, request, pk=None):
        """Desvincula um profissional do campeonato"""
        campeonato = self.get_object()
        profissional_id = request.data.get('profissional_id')
        
        if not profissional_id:
            return Response({'error': 'profissional_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vinculo = ProfissionalCampeonato.objects.get(
                profissional_id=profissional_id,
                campeonato=campeonato
            )
            vinculo.delete()
            return Response({'message': 'Profissional desvinculado com sucesso'}, status=status.HTTP_204_NO_CONTENT)
        except ProfissionalCampeonato.DoesNotExist:
            return Response({'error': 'Vínculo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'], url_path='editar_vinculo_profissional')
    def editar_vinculo_profissional(self, request, pk=None):
        """Edita o vínculo entre profissional e campeonato (incluindo função)"""
        campeonato = self.get_object()
        profissional_id = request.data.get('profissional_id')
        funcao_principal = request.data.get('funcao_principal')
        
        if not profissional_id:
            return Response({'error': 'profissional_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not funcao_principal:
            return Response({'error': 'funcao_principal é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vinculo = ProfissionalCampeonato.objects.get(
                profissional_id=profissional_id,
                campeonato=campeonato
            )
            vinculo.funcao_principal = funcao_principal
            vinculo.save()
            
            serializer = ProfissionalCampeonatoSerializer(vinculo)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ProfissionalCampeonato.DoesNotExist:
            return Response({'error': 'Vínculo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='gerar_rodadas')
    def gerar_rodadas(self, request, pk=None):
        """Gera automaticamente as rodadas para o campeonato com base no formato"""
        print(f"=== INÍCIO GERAR RODADAS ===")
        print(f"Request user: {request.user}")
        print(f"Request user authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}")
        print(f"Session keys: {list(request.session.keys()) if hasattr(request, 'session') else 'N/A'}")
        
        tenant = self.get_tenant()
        print(f"Tenant encontrado: {tenant}")
        
        campeonato = self.get_object()
        print(f"Campeonato: {campeonato.nome} (ID: {campeonato.id})")
        
        times = TimeCampeonato.objects.filter(campeonato=campeonato)
        print(f"Times encontrados: {times.count()}")
        
        # Verificar se há times suficientes
        if times.count() < 2:
            return Response(
                {'error': f'É necessário ter pelo menos 2 times para gerar rodadas. Atualmente há {times.count()} time(s) vinculado(s).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se a data de início está definida
        if not campeonato.data_inicio:
            return Response(
                {'error': 'A data de início do campeonato não está definida. Por favor, defina uma data de início.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Excluir rodadas existentes se houver
        rodadas_existentes = Rodada.objects.filter(campeonato=campeonato).count()
        Rodada.objects.filter(campeonato=campeonato).delete()
        
        # Log para debug
        print(f"Gerando rodadas para campeonato: {campeonato.nome} (ID: {campeonato.id})")
        print(f"Formato: {campeonato.tipo_formato} | Times: {times.count()} | Rodadas existentes: {rodadas_existentes}")
        
        # Listar times para debug
        for i, time in enumerate(times):
            print(f"Time {i+1}: {time.time.nome} (ID: {time.time.id})")
          # Quantidade de rodadas baseada no formato
        if campeonato.tipo_formato == 'liga':
            # Para liga (pontos corridos), cada time joga contra todos os outros
            # Se for ida e volta, multiplica por 2
            num_times = times.count()
            
            # Ajustar para número par ou ímpar de times
            num_rodadas = num_times if num_times % 2 == 1 else num_times - 1
            
            if campeonato.ida_volta:
                num_rodadas *= 2
                
            print(f"Liga: {num_times} times | {num_rodadas} rodadas | Ida e volta: {campeonato.ida_volta}")
            
            # Criar rodadas
            data_atual = campeonato.data_inicio
            rodadas_criadas = []
            
            for i in range(1, num_rodadas + 1):
                rodada = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=i,
                    data=data_atual
                )
                rodadas_criadas.append(rodada)
                # Avançar 7 dias para a próxima rodada
                data_atual += timedelta(days=7)
                
        elif campeonato.tipo_formato == 'mata_mata':            # Para mata-mata, o número de rodadas depende do número de times
            num_times = times.count()
            num_rodadas = 0
            fases = []
            times_restantes = num_times

            while times_restantes > 1:
                times_restantes = times_restantes // 2
                num_rodadas += 1
                fases.append(times_restantes)
            print(f"Mata-mata: {num_times} times | {num_rodadas} rodadas | Ida e volta: {campeonato.ida_volta}")
            data_atual = campeonato.data_inicio
            rodadas_criadas = []
            
            # Função para determinar o nome correto da fase baseado no número de times na fase
            def obter_nome_fase_mata_mata(times_na_fase):
                if times_na_fase == 2:
                    return "Final"
                elif times_na_fase == 4:
                    return "Semifinal"
                elif times_na_fase == 8:
                    return "Quartas de Final"
                elif times_na_fase == 16:
                    return "Oitavas de Final"
                elif times_na_fase == 32:
                    return "Fase de 32"
                elif times_na_fase == 64:
                    return "Fase de 64"
                else:
                    return f"Fase de {times_na_fase}"
            
            # Calcular times por fase (começando do número inicial)
            times_por_fase = num_times
            for i in range(1, num_rodadas + 1):
                nome_rodada = obter_nome_fase_mata_mata(times_por_fase)
                # Ida
                rodada_ida = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=(i-1)*2+1,
                    data=data_atual,
                    observacoes=f"{nome_rodada} - Ida"
                )
                rodadas_criadas.append(rodada_ida)
                data_atual += timedelta(days=7)
                # Volta
                if campeonato.ida_volta:
                    rodada_volta = Rodada.objects.create(
                        campeonato=campeonato,
                        numero=(i-1)*2+2,
                        data=data_atual,
                        observacoes=f"{nome_rodada} - Volta"
                    )
                    rodadas_criadas.append(rodada_volta)
                    data_atual += timedelta(days=7)
                # Reduzir pela metade para a próxima fase
                times_por_fase = times_por_fase // 2
            # Disputa de 3º lugar
            if campeonato.disputa_terceiro:
                rodada_terceiro = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=len(rodadas_criadas)+1,
                    data=data_atual,
                    observacoes="Disputa de 3º Lugar"
                )
                rodadas_criadas.append(rodada_terceiro)
                data_atual += timedelta(days=7)
                
        elif campeonato.tipo_formato == 'grupos':
            # Para grupos, primeiro fase de grupos, depois mata-mata
            num_grupos = campeonato.num_grupos or 2
            
            # Validar número de grupos
            if num_grupos < 2:
                return Response(
                    {'error': 'O número de grupos deve ser pelo menos 2'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar se há times suficientes para os grupos
            if times.count() < num_grupos * 2:
                return Response(
                    {'error': f'São necessários pelo menos {num_grupos * 2} times para {num_grupos} grupos (mínimo 2 times por grupo)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            times_por_grupo = times.count() // num_grupos
            
            # Fase de grupos (todos contra todos dentro do grupo)
            rodadas_grupo = times_por_grupo - 1
            if campeonato.ida_volta:
                rodadas_grupo *= 2
            
            # Fase eliminatória (com base no número de classificados por grupo)
            num_classificados = campeonato.num_classificados or 2
            times_classificados = num_grupos * num_classificados
            
            # Validar número de classificados
            if times_classificados < 2:
                return Response(
                    {'error': 'O número total de classificados deve ser pelo menos 2'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if times_classificados > times.count():
                times_classificados = times.count()
                
            # Calcular rodadas da fase eliminatória
            rodadas_eliminatorias = 0
            times_restantes = times_classificados
            while times_restantes > 1:
                times_restantes = times_restantes // 2
                rodadas_eliminatorias += 1
            
            # Total de rodadas
            num_rodadas = rodadas_grupo + rodadas_eliminatorias
            
            print(f"Grupos: {num_grupos} grupos | {times_por_grupo} times por grupo | {rodadas_grupo} rodadas fase de grupos | {rodadas_eliminatorias} rodadas eliminatórias")
            
            # Criar rodadas
            data_atual = campeonato.data_inicio
            rodadas_criadas = []
              # Criar rodadas da fase de grupos
            for i in range(1, rodadas_grupo + 1):
                rodada = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=i,
                    data=data_atual,
                    observacoes=f"Fase de Grupos - Rodada {i}"
                )
                rodadas_criadas.append(rodada)
                # Avançar 7 dias para a próxima rodada
                data_atual += timedelta(days=7)

            # Criar rodadas da fase eliminatória
            # Função para determinar o nome correto da fase baseado no número de times classificados
            def obter_nome_fase(times_na_fase):
                if times_na_fase == 2:
                    return "Final"
                elif times_na_fase == 4:
                    return "Semifinal"
                elif times_na_fase == 8:
                    return "Quartas de Final"
                elif times_na_fase == 16:
                    return "Oitavas de Final"
                elif times_na_fase == 32:
                    return "Fase de 32"
                elif times_na_fase == 64:
                    return "Fase de 64"
                else:
                    return f"Fase de {times_na_fase}"
            
            if rodadas_eliminatorias == 1:
                # Só uma fase eliminatória: Final
                nome_fase = "Final"
                rodada_ida = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=rodadas_grupo + 1,
                    data=data_atual,
                    observacoes=f"{nome_fase} - Ida" if campeonato.ida_volta else nome_fase
                )
                rodadas_criadas.append(rodada_ida)
                data_atual += timedelta(days=7)
                if campeonato.ida_volta:
                    rodada_volta = Rodada.objects.create(
                        campeonato=campeonato,
                        numero=rodadas_grupo + 2,
                        data=data_atual,
                        observacoes=f"{nome_fase} - Volta"
                    )
                    rodadas_criadas.append(rodada_volta)
                    data_atual += timedelta(days=7)
            elif rodadas_eliminatorias > 1:
                # Calcular quantos times estão em cada fase
                times_por_fase = times_classificados
                for i in range(rodadas_eliminatorias):
                    nome_fase = obter_nome_fase(times_por_fase)
                    # Ida
                    rodada_ida = Rodada.objects.create(
                        campeonato=campeonato,
                        numero=rodadas_grupo + i * (2 if campeonato.ida_volta else 1) + 1,
                        data=data_atual,
                        observacoes=f"{nome_fase} - Ida" if campeonato.ida_volta else nome_fase
                    )
                    rodadas_criadas.append(rodada_ida)
                    data_atual += timedelta(days=7)
                    # Volta
                    if campeonato.ida_volta:
                        rodada_volta = Rodada.objects.create(
                            campeonato=campeonato,
                            numero=rodadas_grupo + i * 2 + 2,
                            data=data_atual,
                            observacoes=f"{nome_fase} - Volta"
                        )
                        rodadas_criadas.append(rodada_volta)
                        data_atual += timedelta(days=7)
                    # Reduzir pela metade para a próxima fase
                    times_por_fase = times_por_fase // 2
            # Disputa de 3º lugar
            if campeonato.disputa_terceiro and rodadas_eliminatorias >= 2:
                rodada_terceiro = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=len(rodadas_criadas)+1,
                    data=data_atual,
                    observacoes="Disputa de 3º Lugar"
                )
                rodadas_criadas.append(rodada_terceiro)
                data_atual += timedelta(days=7)
                
        elif campeonato.tipo_formato == 'misto':
            # Para misto: fase de grupos + mata-mata (similar ao formato grupos)
            num_grupos = campeonato.num_grupos or 2
            
            # Validar número de grupos
            if num_grupos < 2:
                return Response(
                    {'error': 'O número de grupos deve ser pelo menos 2'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar se há times suficientes para os grupos
            if times.count() < num_grupos * 2:
                return Response(
                    {'error': f'São necessários pelo menos {num_grupos * 2} times para {num_grupos} grupos (mínimo 2 times por grupo)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            times_por_grupo = times.count() // num_grupos
            
            # Fase de grupos (todos contra todos dentro do grupo)
            # Para 3 times por grupo: 3 partidas por grupo
            rodadas_grupo = times_por_grupo - 1
            if campeonato.ida_volta:
                rodadas_grupo *= 2
            
            # Fase eliminatória (com base no número de classificados por grupo)
            num_classificados = campeonato.num_classificados or 2
            times_classificados = num_grupos * num_classificados
            
            # Validar número de classificados
            if times_classificados < 2:
                return Response(
                    {'error': 'O número total de classificados deve ser pelo menos 2'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if times_classificados > times.count():
                times_classificados = times.count()
                
            # Calcular rodadas da fase eliminatória
            rodadas_eliminatorias = 0
            times_restantes = times_classificados
            while times_restantes > 1:
                times_restantes = times_restantes // 2
                rodadas_eliminatorias += 1
            
            # Total de rodadas
            num_rodadas = rodadas_grupo + rodadas_eliminatorias
            
            print(f"Misto: {num_grupos} grupos | {times_por_grupo} times por grupo | {rodadas_grupo} rodadas fase de grupos | {rodadas_eliminatorias} rodadas eliminatórias")
            
            # Criar rodadas
            data_atual = campeonato.data_inicio
            rodadas_criadas = []
            
            # Criar rodadas da fase de grupos
            for i in range(1, rodadas_grupo + 1):
                rodada = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=i,
                    data=data_atual,
                    observacoes=f"Fase de Grupos - Rodada {i}"
                )
                rodadas_criadas.append(rodada)
                data_atual += timedelta(days=7)

            # Criar rodadas da fase eliminatória
            def obter_nome_fase_misto(times_na_fase):
                if times_na_fase == 2:
                    return "Final"
                elif times_na_fase == 4:
                    return "Semifinal"
                elif times_na_fase == 8:
                    return "Quartas de Final"
                elif times_na_fase == 16:
                    return "Oitavas de Final"
                else:
                    return f"Fase de {times_na_fase}"
            
            if rodadas_eliminatorias == 1:
                # Só uma fase eliminatória: Final
                nome_fase = "Final"
                rodada_ida = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=rodadas_grupo + 1,
                    data=data_atual,
                    observacoes=f"{nome_fase} - Ida" if campeonato.ida_volta else nome_fase
                )
                rodadas_criadas.append(rodada_ida)
                data_atual += timedelta(days=7)
                if campeonato.ida_volta:
                    rodada_volta = Rodada.objects.create(
                        campeonato=campeonato,
                        numero=rodadas_grupo + 2,
                        data=data_atual,
                        observacoes=f"{nome_fase} - Volta"
                    )
                    rodadas_criadas.append(rodada_volta)
                    data_atual += timedelta(days=7)
            elif rodadas_eliminatorias > 1:
                # Calcular quantos times estão em cada fase
                times_por_fase = times_classificados
                for i in range(rodadas_eliminatorias):
                    nome_fase = obter_nome_fase_misto(times_por_fase)
                    # Ida
                    rodada_ida = Rodada.objects.create(
                        campeonato=campeonato,
                        numero=rodadas_grupo + i * (2 if campeonato.ida_volta else 1) + 1,
                        data=data_atual,
                        observacoes=f"{nome_fase} - Ida" if campeonato.ida_volta else nome_fase
                    )
                    rodadas_criadas.append(rodada_ida)
                    data_atual += timedelta(days=7)
                    # Volta
                    if campeonato.ida_volta:
                        rodada_volta = Rodada.objects.create(
                            campeonato=campeonato,
                            numero=rodadas_grupo + i * 2 + 2,
                            data=data_atual,
                            observacoes=f"{nome_fase} - Volta"
                        )
                        rodadas_criadas.append(rodada_volta)
                        data_atual += timedelta(days=7)
                    # Reduzir pela metade para a próxima fase
                    times_por_fase = times_por_fase // 2
            
            # Disputa de 3º lugar para misto
            if campeonato.disputa_terceiro and rodadas_eliminatorias >= 2:
                rodada_terceiro = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=len(rodadas_criadas)+1,
                    data=data_atual,
                    observacoes="Disputa de 3º Lugar"
                )
                rodadas_criadas.append(rodada_terceiro)
                data_atual += timedelta(days=7)
                
        else:
            # Formato padrão para outros casos (divisões, etc)
            # Criamos um número padrão de rodadas
            num_rodadas = times.count()
            print(f"Outro formato: {campeonato.tipo_formato} | {num_rodadas} rodadas")
            data_atual = campeonato.data_inicio
            rodadas_criadas = []
            for i in range(1, num_rodadas + 1):
                rodada = Rodada.objects.create(
                    campeonato=campeonato,
                    numero=i,
                    data=data_atual,
                    observacoes=f"Rodada {i}"
                )
                rodadas_criadas.append(rodada)
                data_atual += timedelta(days=7)
        
        # Retornar as rodadas criadas
        rodadas = Rodada.objects.filter(campeonato=campeonato).order_by('numero')
        if not rodadas.exists():
            return Response(
                {'error': 'Não foi possível gerar as rodadas. Verifique os parâmetros do campeonato.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = RodadaSerializer(rodadas, many=True)
        return Response({
            'message': f'Foram geradas {rodadas.count()} rodadas com sucesso!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='gerar_todas_partidas')
    def gerar_todas_partidas(self, request, pk=None):
        """Gera automaticamente todas as partidas para todas as rodadas do campeonato"""
        campeonato = self.get_object()
        times = list(TimeCampeonato.objects.filter(campeonato=campeonato))
        
        if len(times) < 2:
            return Response(
                {'error': 'É necessário pelo menos 2 times para gerar partidas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar todas as rodadas do campeonato
        rodadas = Rodada.objects.filter(campeonato=campeonato).order_by('numero')
        
        if not rodadas.exists():
            return Response(
                {'error': 'Nenhuma rodada encontrada. Gere as rodadas primeiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total_partidas_criadas = 0
        
        # Gerar partidas para cada rodada
        for rodada in rodadas:
            # Remove partidas existentes da rodada
            Partida.objects.filter(rodada=rodada).delete()
            
            partidas_criadas = []
            
            # Lógica específica por formato de campeonato
            if campeonato.tipo_formato == 'grupos':
                partidas_criadas = self._gerar_partidas_grupos_completo(rodada, campeonato, times)
            elif campeonato.tipo_formato == 'mata_mata':
                partidas_criadas = self._gerar_partidas_mata_mata_completo(rodada, campeonato, times)
            elif campeonato.tipo_formato == 'liga':
                partidas_criadas = self._gerar_partidas_liga_completo(rodada, campeonato, times)
            elif campeonato.tipo_formato == 'misto':
                partidas_criadas = self._gerar_partidas_grupos_completo(rodada, campeonato, times)
            else:
                # Para formatos divisões ou outros
                partidas_criadas = self._gerar_partidas_dinamica_completo(rodada, campeonato, times)
            
            total_partidas_criadas += len(partidas_criadas)
        
        return Response({
            'message': f'Foram geradas {total_partidas_criadas} partidas em {rodadas.count()} rodadas com sucesso!'
        }, status=status.HTTP_201_CREATED)
    
    def _gerar_partidas_grupos_completo(self, rodada, campeonato, times):
        """Gera partidas completas para formato de grupos"""
        partidas_criadas = []
        nome_rodada = rodada.observacoes or ''
        
        if 'Fase de Grupos' in nome_rodada:
            # Fase de grupos: dividir times em grupos
            num_grupos = campeonato.num_grupos or 2
            times_por_grupo = len(times) // num_grupos
            
            # Organizar times em grupos
            grupos = []
            for i in range(num_grupos):
                inicio = i * times_por_grupo
                fim = inicio + times_por_grupo
                if i == num_grupos - 1:  # Último grupo pega os times restantes
                    grupo_times = times[inicio:]
                else:
                    grupo_times = times[inicio:fim]
                
                grupos.append({
                    'letra': chr(65 + i),
                    'times': grupo_times
                })
            
            # Para cada grupo, gerar partidas da rodada atual
            numero_rodada = rodada.numero
            
            # Verificar se confrontos são dentro do mesmo grupo ou entre grupos diferentes
            if getattr(campeonato, 'confrontos_mesmo_grupo', True):
                # Confrontos dentro do mesmo grupo (padrão)
                for grupo_idx, grupo in enumerate(grupos):
                    if len(grupo['times']) < 2:
                        continue
                        
                    # Gerar confrontos usando sistema round-robin para a rodada específica
                    confrontos_rodada = self._gerar_confrontos_round_robin(grupo['times'], numero_rodada)
                    
                    for time_casa, time_visitante in confrontos_rodada:
                        partida = Partida.objects.create(
                            rodada=rodada,
                            time_mandante=time_casa,
                            time_visitante=time_visitante,
                            data_hora=rodada.data or None,
                            local='',
                            observacoes=f'Grupo {grupo["letra"]}'
                        )
                        partidas_criadas.append(partida)
            else:
                # Confrontos entre grupos diferentes
                # Implementar lógica para confrontos inter-grupos
                # Por exemplo: times do Grupo A vs times do Grupo B, etc.
                for i in range(num_grupos):
                    for j in range(i + 1, num_grupos):
                        grupo_a = grupos[i]
                        grupo_b = grupos[j]
                        
                        # Gerar confrontos entre os grupos
                        for idx_a, time_a in enumerate(grupo_a['times']):
                            for idx_b, time_b in enumerate(grupo_b['times']):
                                # Usar número da rodada para determinar quais confrontos gerar
                                if (idx_a + idx_b + numero_rodada) % 2 == 0:
                                    partida = Partida.objects.create(
                                        rodada=rodada,
                                        time_mandante=time_a,
                                        time_visitante=time_b,
                                        data_hora=rodada.data or None,
                                        local='',
                                        observacoes=f'Grupo {grupo_a["letra"]} vs Grupo {grupo_b["letra"]}'
                                    )
                                    partidas_criadas.append(partida)
        else:
            # Fase eliminatória: gerar com participantes genéricos
            partidas_criadas = self._gerar_partidas_eliminatoria_completo(rodada, campeonato, times)
            
        return partidas_criadas
    
    def _gerar_partidas_mata_mata_completo(self, rodada, campeonato, times):
        """Gera partidas completas para formato mata-mata"""
        return self._gerar_partidas_eliminatoria_completo(rodada, campeonato, times)
    
    def _gerar_partidas_liga_completo(self, rodada, campeonato, times):
        """Gera partidas completas para formato liga"""
        partidas_criadas = []
        numero_rodada = rodada.numero
        
        # Gerar confrontos usando sistema round-robin para a rodada específica
        confrontos_rodada = self._gerar_confrontos_round_robin(times, numero_rodada)
        
        for time_casa, time_visitante in confrontos_rodada:
            partida = Partida.objects.create(
                rodada=rodada,
                time_mandante=time_casa,
                time_visitante=time_visitante,
                data_hora=rodada.data or None,
                local=''
            )
            partidas_criadas.append(partida)
            
        return partidas_criadas
    
    def _gerar_partidas_dinamica_completo(self, rodada, campeonato, times):
        """Gera partidas completas baseado no nome/contexto da rodada"""
        nome_rodada = rodada.observacoes or ''
        
        if 'Fase de Grupos' in nome_rodada or 'Rodada' in nome_rodada:
            return self._gerar_partidas_liga_completo(rodada, campeonato, times)
        else:
            return self._gerar_partidas_eliminatoria_completo(rodada, campeonato, times)
    
    def _gerar_partidas_eliminatoria_completo(self, rodada, campeonato, times):
        """Gera partidas completas para fases eliminatórias"""
        partidas_criadas = []
        nome_rodada = rodada.observacoes or ''
        
        # Determinar número de partidas baseado no nome da fase
        if 'Final' in nome_rodada and 'Semifinal' not in nome_rodada:
            num_partidas = 1
            participante_prefixo = "Vencedor da Semifinal"
        elif 'Semifinal' in nome_rodada:
            num_partidas = 2
            participante_prefixo = "Classificado"
        elif 'Quartas' in nome_rodada:
            num_partidas = 4
            participante_prefixo = "Classificado"
        elif 'Oitavas' in nome_rodada:
            num_partidas = 8
            participante_prefixo = "Classificado"
        elif 'Disputa de 3º Lugar' in nome_rodada:
            num_partidas = 1
            participante_prefixo = "Perdedor da Semifinal"
        else:
            # Para outras fases, calcular baseado no número de times
            num_partidas = len(times) // 2
            participante_prefixo = "Classificado"
        
        # Verificar se é a primeira fase eliminatória (após grupos ou primeira rodada)
        rodadas_anteriores_eliminatorias = Rodada.objects.filter(
            campeonato=campeonato,
            numero__lt=rodada.numero
        ).exclude(observacoes__icontains='Fase de Grupos').exists()
        
        if not rodadas_anteriores_eliminatorias and ('Oitavas' in nome_rodada or 'Quartas' in nome_rodada or 
                                                     (campeonato.tipo_formato == 'mata_mata' and rodada.numero == 1)):
            # Primeira fase eliminatória com times reais
            for i in range(0, min(len(times), num_partidas * 2), 2):
                if i + 1 < len(times):
                    partida = Partida.objects.create(
                        rodada=rodada,
                        time_mandante=times[i],
                        time_visitante=times[i + 1],
                        data_hora=rodada.data or None,
                        local=''
                    )
                    partidas_criadas.append(partida)
        else:
            # Fases posteriores com participantes genéricos
            for i in range(num_partidas):
                if 'Final' in nome_rodada and 'Semifinal' not in nome_rodada:
                    observacao = f'{participante_prefixo} 1 vs {participante_prefixo} 2'
                elif 'Disputa de 3º Lugar' in nome_rodada:
                    observacao = f'{participante_prefixo} 1 vs {participante_prefixo} 2'
                else:
                    observacao = f'{participante_prefixo} {i*2+1} vs {participante_prefixo} {i*2+2}'
                
                partida = Partida.objects.create(
                    rodada=rodada,
                    time_mandante=None,
                    time_visitante=None,
                    data_hora=rodada.data or None,
                    local='',
                    observacoes=observacao
                )
                partidas_criadas.append(partida)
        
        return partidas_criadas

    @action(detail=True, methods=['get'], url_path='rodadas')
    def rodadas(self, request, pk=None):
        """Lista as rodadas do campeonato"""
        campeonato = self.get_object()
        rodadas = Rodada.objects.filter(campeonato=campeonato).order_by('numero')
        serializer = RodadaSerializer(rodadas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='profissionais_disponiveis')
    def profissionais_disponiveis(self, request, pk=None):
        """Retorna profissionais vinculados ao campeonato disponíveis para serem designados a partidas"""
        campeonato = self.get_object()
        profissionais_campeonato = ProfissionalCampeonato.objects.filter(campeonato=campeonato)
        serializer = ProfissionalCampeonatoSerializer(profissionais_campeonato, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='composicao_grupos')
    def composicao_grupos(self, request, pk=None):
        """Retorna a composição dos grupos para campeonatos de grupos ou misto"""
        campeonato = self.get_object()
        times = list(TimeCampeonato.objects.filter(campeonato=campeonato))
        
        if campeonato.tipo_formato not in ['grupos', 'misto']:
            return Response(
                {'error': 'Este campeonato não possui formato de grupos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(times) < 2:
            return Response(
                {'error': 'É necessário pelo menos 2 times para formar grupos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        num_grupos = campeonato.num_grupos or 2
        times_por_grupo = len(times) // num_grupos
        
        # Organizar times em grupos (mesma lógica usada na geração de partidas)
        grupos = []
        for i in range(num_grupos):
            inicio = i * times_por_grupo
            fim = inicio + times_por_grupo
            if i == num_grupos - 1:  # Último grupo pega os times restantes
                grupo_times = times[inicio:]
            else:
                grupo_times = times[inicio:fim]
            
            grupo = {
                'nome': f'Grupo {chr(65 + i)}',  # A, B, C, etc.
                'letra': chr(65 + i),
                'times': [
                    {
                        'id': time.id,
                        'time_id': time.time.id,
                        'nome': time.time.nome,
                        'escudo_url': time.time.escudo.url if time.time.escudo else None
                    }
                    for time in grupo_times
                ]
            }
            grupos.append(grupo)
        
        return Response({
            'num_grupos': num_grupos,
            'times_por_grupo': times_por_grupo,
            'grupos': grupos
        })


class TimeCampeonatoViewSet(viewsets.ModelViewSet):
    queryset = TimeCampeonato.objects.all().order_by('id')
    serializer_class = TimeCampeonatoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = None
        try:
            tenant = Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            pass

        if tenant:
            return self.queryset.filter(campeonato__tenant=tenant).order_by('id')
        return self.queryset.none()

    @action(detail=True, methods=['get'])
    def jogadores(self, request, pk=None):
        """Retorna jogadores vinculados ao TimeCampeonato"""
        time_campeonato = self.get_object()
        vinculos_ativos = JogadorTimeCampeonato.objects.filter(
            time_campeonato=time_campeonato,
            ativo=True
        )
        serializer = JogadorTimeCampeonatoSerializer(vinculos_ativos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='vincular_jogador')
    def vincular_jogador(self, request, pk=None):
        """Vincula um jogador ao time no campeonato"""
        time_campeonato = self.get_object()
        jogador_id = request.data.get('jogador_id')

        if not jogador_id:
            return Response(
                {'error': 'jogador_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(usuario=request.user)
            jogador = Jogador.objects.get(id=jogador_id, tenant=tenant)
        except (Tenant.DoesNotExist, Jogador.DoesNotExist):
            return Response(
                {'error': 'Jogador não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar se já está vinculado e ativo
        if JogadorTimeCampeonato.objects.filter(
            jogador=jogador,
            time_campeonato=time_campeonato,
            ativo=True
        ).exists():
            return Response(
                {'error': 'Jogador já está vinculado a este time'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Criar vinculação
        jogador_time = JogadorTimeCampeonato.objects.create(
            jogador=jogador,
            time_campeonato=time_campeonato
        )

        serializer = JogadorTimeCampeonatoSerializer(jogador_time)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='desvincular_jogador')
    def desvincular_jogador(self, request, pk=None):
        """Desvincula um jogador do time no campeonato"""
        time_campeonato = self.get_object()
        jogador_id = request.data.get('jogador_id')

        if not jogador_id:
            return Response(
                {'error': 'jogador_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vinculo = JogadorTimeCampeonato.objects.get(
                jogador_id=jogador_id,
                time_campeonato=time_campeonato,
                ativo=True
            )
            vinculo.ativo = False
            vinculo.data_saida = timezone.now().date()
            vinculo.save()

            return Response({'message': 'Jogador desvinculado com sucesso'})
        except JogadorTimeCampeonato.DoesNotExist:
            return Response(
                {'error': 'Vínculo não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class RodadaViewSet(viewsets.ModelViewSet):
    queryset = Rodada.objects.all().order_by('id')
    serializer_class = RodadaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = None
        try:
            tenant = Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            tenant = None

        if tenant:
            return self.queryset.filter(campeonato__tenant=tenant).order_by('id')
        return self.queryset.none()

    @action(detail=True, methods=['get'], url_path='partidas')
    def partidas(self, request, pk=None):
        """Retorna as partidas da rodada"""
        rodada = self.get_object()
        partidas = rodada.partidas.all().order_by('data_hora', 'id')
        serializer = PartidaSerializer(partidas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='gerar_partidas')
    def gerar_partidas(self, request, pk=None):
        """Gera automaticamente as partidas para a rodada"""
        rodada = self.get_object()
        campeonato = rodada.campeonato
        times = list(TimeCampeonato.objects.filter(campeonato=campeonato))
        if len(times) < 2:
            return Response({'error': 'É necessário pelo menos 2 times para gerar partidas.'}, status=400)

        # Remove partidas existentes da rodada
        Partida.objects.filter(rodada=rodada).delete()

        partidas_criadas = []
        
        # Lógica específica por formato de campeonato
        if campeonato.tipo_formato == 'grupos':
            partidas_criadas = self._gerar_partidas_grupos(rodada, campeonato, times)
        elif campeonato.tipo_formato == 'mata_mata':
            partidas_criadas = self._gerar_partidas_mata_mata(rodada, campeonato, times)
        elif campeonato.tipo_formato == 'liga':
            partidas_criadas = self._gerar_partidas_liga(rodada, campeonato, times)
        elif campeonato.tipo_formato == 'misto':
            partidas_criadas = self._gerar_partidas_grupos(rodada, campeonato, times)
        else:
            # Para formatos divisões ou outros, usar lógica padrão baseada no nome da rodada
            partidas_criadas = self._gerar_partidas_dinamica(rodada, campeonato, times)
            
        return Response({'message': f'{len(partidas_criadas)} partidas geradas com sucesso.'}, status=201)
    
    def _gerar_partidas_grupos(self, rodada, campeonato, times):
        """Gera partidas para formato de grupos"""
        partidas_criadas = []
        
        # Verificar se é fase de grupos ou fase eliminatória
        nome_rodada = rodada.observacoes or ''
        
        if 'Fase de Grupos' in nome_rodada:
            # Fase de grupos: dividir times em grupos e fazer confrontos dentro do grupo
            num_grupos = campeonato.num_grupos or 2
            times_por_grupo = len(times) // num_grupos
            
            # Organizar times em grupos
            grupos = []
            for i in range(num_grupos):
                inicio = i * times_por_grupo
                fim = inicio + times_por_grupo
                if i == num_grupos - 1:  # Último grupo pega os times restantes
                    grupo = times[inicio:]
                else:
                    grupo = times[inicio:fim]
                grupos.append(grupo)
            
            # Para cada grupo, gerar partidas da rodada atual
            numero_rodada = rodada.numero
            
            for grupo_idx, times_grupo in enumerate(grupos):
                if len(times_grupo) < 2:
                    continue
                    
                # Gerar confrontos usando sistema round-robin para a rodada específica
                confrontos_rodada = self._gerar_confrontos_round_robin(times_grupo, numero_rodada)
                
                for time_casa, time_visitante in confrontos_rodada:
                    partida = Partida.objects.create(
                        rodada=rodada,
                        time_mandante=time_casa,
                        time_visitante=time_visitante,
                        data_hora=rodada.data or None,
                        local=''
                    )
                    partidas_criadas.append(partida)
        else:
            # Fase eliminatória: usar participantes genéricos
            partidas_criadas = self._gerar_partidas_eliminatoria(rodada, campeonato, times)
            
        return partidas_criadas
    
    def _gerar_partidas_mata_mata(self, rodada, campeonato, times):
        """Gera partidas para formato mata-mata"""
        return self._gerar_partidas_eliminatoria(rodada, campeonato, times)
    
    def _gerar_partidas_liga(self, rodada, campeonato, times):
        """Gera partidas para formato liga (pontos corridos)"""
        partidas_criadas = []
        numero_rodada = rodada.numero
        
        # Gerar confrontos usando sistema round-robin para a rodada específica
        confrontos_rodada = self._gerar_confrontos_round_robin(times, numero_rodada)
        
        for time_casa, time_visitante in confrontos_rodada:
            partida = Partida.objects.create(
                rodada=rodada,
                time_mandante=time_casa,
                time_visitante=time_visitante,
                data_hora=rodada.data or None,
                local=''
            )
            partidas_criadas.append(partida)
            
        return partidas_criadas
    
    def _gerar_partidas_dinamica(self, rodada, campeonato, times):
        """Gera partidas baseado no nome/contexto da rodada"""
        nome_rodada = rodada.observacoes or ''
        
        if 'Fase de Grupos' in nome_rodada or 'Rodada' in nome_rodada:
            return self._gerar_partidas_liga(rodada, campeonato, times)
        else:
            return self._gerar_partidas_eliminatoria(rodada, campeonato, times)
    
    def _gerar_partidas_eliminatoria(self, rodada, campeonato, times):
        """Gera partidas para fases eliminatórias"""
        partidas_criadas = []
        nome_rodada = rodada.observacoes or ''
        
        # Determinar número de partidas baseado no nome da fase
        if 'Final' in nome_rodada:
            num_partidas = 1
        elif 'Semifinal' in nome_rodada:
            num_partidas = 2
        elif 'Quartas' in nome_rodada:
            num_partidas = 4
        elif 'Oitavas' in nome_rodada:
            num_partidas = 8
        else:
            # Para outras fases, calcular baseado no número de times disponíveis
            num_partidas = len(times) // 2
        
        # Verificar se é primeira rodada (times reais) ou rodadas posteriores (participantes genéricos)
        rodadas_anteriores = Rodada.objects.filter(
            campeonato=campeonato,
            numero__lt=rodada.numero
        ).exists()
        
        if not rodadas_anteriores or len(times) >= num_partidas * 2:
            # Primeira fase com times reais
            for i in range(0, min(len(times), num_partidas * 2), 2):
                if i + 1 < len(times):
                    partida = Partida.objects.create(
                        rodada=rodada,
                        time_mandante=times[i],
                        time_visitante=times[i + 1],
                        data_hora=rodada.data or None,
                        local=''
                    )
                    partidas_criadas.append(partida)
        else:
            # Fases posteriores com participantes genéricos - criar partidas vazias
            for i in range(num_partidas):
                partida = Partida.objects.create(
                    rodada=rodada,
                    time_mandante=None,  # Será preenchido quando a fase anterior terminar
                    time_visitante=None,  # Será preenchido quando a fase anterior terminar
                    data_hora=rodada.data or None,
                    local='',
                    observacoes=f'Aguardando definição dos classificados da fase anterior'
                )
                partidas_criadas.append(partida)
        
        return partidas_criadas
    
    def _gerar_confrontos_round_robin(self, times, numero_rodada):
        """Gera confrontos para uma rodada específica usando algoritmo round-robin"""
        n = len(times)
        if n < 2:
            return []
        
        # Se número ímpar de times, adicionar time "fantasma"
        if n % 2 == 1:
            times = times + [None]
            n += 1
        
        # Algoritmo round-robin
        confrontos = []
        for rodada in range(1, n):
            rodada_confrontos = []
            for i in range(n // 2):
                time1_idx = i
                time2_idx = n - 1 - i
                
                if rodada == numero_rodada:
                    time1 = times[time1_idx]
                    time2 = times[time2_idx]
                    
                    # Verificar se não é time fantasma
                    if time1 is not None and time2 is not None:
                        confrontos.append((time1, time2))
            
            # Rotacionar times (exceto o primeiro)
            times = [times[0]] + [times[-1]] + times[1:-1]
        
        return confrontos


class PartidaViewSet(viewsets.ModelViewSet):
    queryset = Partida.objects.all().order_by('id')
    serializer_class = PartidaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = None
        try:
            tenant = Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            pass

        if tenant:
            return self.queryset.filter(rodada__campeonato__tenant=tenant).order_by('id')
        return self.queryset.none()

    @action(detail=True, methods=['get'])
    def detalhes(self, request, pk=None):
        """Retorna detalhes completos da partida com gols, cartões e profissionais"""
        partida = self.get_object()

        gols = Gol.objects.filter(partida=partida).order_by('minuto')
        cartoes = Cartao.objects.filter(partida=partida).order_by('minuto')
        profissionais = ProfissionalPartida.objects.filter(partida=partida)

        return Response({
            'partida': PartidaSerializer(partida).data,
            'gols': GolSerializer(gols, many=True).data,
            'cartoes': CartaoSerializer(cartoes, many=True).data,
            'profissionais': ProfissionalPartidaSerializer(profissionais, many=True).data
        })    @action(detail=True, methods=['get'])
    def gols(self, request, pk=None):
        """Retorna os gols da partida"""
        partida = self.get_object()
        gols = Gol.objects.filter(partida=partida)
        serializer = GolSerializer(gols, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cartoes(self, request, pk=None):
        """Retorna os cartões da partida"""
        partida = self.get_object()
        cartoes = Cartao.objects.filter(partida=partida)
        serializer = CartaoSerializer(cartoes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def profissionais(self, request, pk=None):
        """Retorna os profissionais designados para a partida"""
        partida = self.get_object()
        profissionais = ProfissionalPartida.objects.filter(partida=partida)
        serializer = ProfissionalPartidaSerializer(profissionais, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='atualizar-profissionais')
    def criar_profissionais(self, request, pk=None):
        """Cria novos profissionais para a partida (substituindo os existentes)"""
        partida = self.get_object()
        
        # Limpar profissionais existentes
        ProfissionalPartida.objects.filter(partida=partida).delete()
        
        # Dados dos novos profissionais
        profissionais_data = request.data.get('profissionais', [])
        
        # Criar novos profissionais para a partida
        profissionais_criados = []
        for prof_data in profissionais_data:
            profissional_id = prof_data.get('profissional_id')
            funcao = prof_data.get('funcao', 'Arbitro')
            valor = prof_data.get('valor', 0)
            
            try:
                # Buscar o profissional vinculado ao campeonato
                prof_campeonato = ProfissionalCampeonato.objects.get(
                    profissional_id=profissional_id,
                    campeonato=partida.rodada.campeonato
                )
                
                # Criar o vínculo com a partida
                prof_partida = ProfissionalPartida.objects.create(
                    profissional_campeonato=prof_campeonato,
                    partida=partida,
                    funcao=funcao,
                    valor=valor,
                    descricao=funcao
                )
                
                profissionais_criados.append(prof_partida)
            except ProfissionalCampeonato.DoesNotExist:
                # Log e ignora profissionais não encontrados
                print(f"Profissional {profissional_id} não encontrado no campeonato")
                continue
            except Exception as e:
                print(f"Erro ao criar profissional: {e}")
                continue
        
        serializer = ProfissionalPartidaSerializer(profissionais_criados, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['delete'], url_path='cartoes/limpar')
    def limpar_cartoes(self, request, pk=None):
        """Limpa todos os cartões da partida"""
        partida = self.get_object()
        
        # Excluir todos os cartões da partida
        cartoes_removidos = Cartao.objects.filter(partida=partida).count()
        Cartao.objects.filter(partida=partida).delete()
        
        return Response({
            'message': f'{cartoes_removidos} cartões removidos da partida',
            'cartoes_removidos': cartoes_removidos
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='gols/limpar')
    def limpar_gols(self, request, pk=None):
        """Limpa todos os gols da partida"""
        partida = self.get_object()
        
        # Excluir todos os gols da partida
        gols_removidos = Gol.objects.filter(partida=partida).count()
        Gol.objects.filter(partida=partida).delete()
        
        return Response({
            'message': f'{gols_removidos} gols removidos da partida',
            'gols_removidos': gols_removidos
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='atualizar_gols')
    def atualizar_gols(self, request, pk=None):
        """Atualiza os gols da partida"""
        partida = self.get_object()
        
        # Excluir gols existentes
        Gol.objects.filter(partida=partida).delete()
        
        # Dados dos novos gols
        gols_data = request.data.get('gols', [])
        
        # Criar novos gols
        gols_criados = []
        for gol_data in gols_data:
            jogador_id = gol_data.get('jogador_id')
            time_id = gol_data.get('time_id')
            
            try:
                # Buscar o vínculo JogadorTimeCampeonato correto
                jogador = JogadorTimeCampeonato.objects.get(
                    jogador_id=jogador_id,
                    time_campeonato_id=time_id,
                    time_campeonato__campeonato=partida.rodada.campeonato,
                    ativo=True
                )
                time = TimeCampeonato.objects.get(
                    id=time_id,
                    campeonato=partida.rodada.campeonato
                )
                
                gol = Gol.objects.create(
                    partida=partida,
                    jogador=jogador,
                    time=time,
                    minuto=gol_data.get('minuto', 0),
                    tipo=gol_data.get('tipo', 'NOR')
                )
                gols_criados.append(gol)
            except (JogadorTimeCampeonato.DoesNotExist, TimeCampeonato.DoesNotExist):
                # Ignorar gols com jogadores ou times inválidos
                pass
        
        # Atualizar placar da partida
        gols_mandante = Gol.objects.filter(partida=partida, time=partida.time_mandante).count()
        gols_visitante = Gol.objects.filter(partida=partida, time=partida.time_visitante).count()
        
        partida.placar_mandante = gols_mandante
        partida.placar_visitante = gols_visitante
        partida.save()
        
        serializer = GolSerializer(gols_criados, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='atualizar_cartoes')
    def atualizar_cartoes(self, request, pk=None):
        """Atualiza os cartões da partida"""
        partida = self.get_object()
        
        # Excluir cartões existentes
        Cartao.objects.filter(partida=partida).delete()
        
        # Dados dos novos cartões
        cartoes_data = request.data.get('cartoes', [])
        
        # Criar novos cartões
        cartoes_criados = []
        for cartao_data in cartoes_data:
            jogador_id = cartao_data.get('jogador_id')
            time_id = cartao_data.get('time_id')
            
            try:
                # Buscar o vínculo JogadorTimeCampeonato correto
                jogador = JogadorTimeCampeonato.objects.get(
                    jogador_id=jogador_id,
                    time_campeonato_id=time_id,
                    time_campeonato__campeonato=partida.rodada.campeonato,
                    ativo=True
                )
                
                cartao = Cartao.objects.create(
                    partida=partida,
                    jogador=jogador,
                    tipo=cartao_data.get('tipo'),  # Já vem como 'AMA' ou 'VER' do frontend
                    minuto=cartao_data.get('minuto', 0),
                    motivo=cartao_data.get('motivo', '')
                )
                cartoes_criados.append(cartao)
                
            except JogadorTimeCampeonato.DoesNotExist:
                # Ignorar cartões com jogadores inválidos
                pass
        
        serializer = CartaoSerializer(cartoes_criados, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet para dados do dashboard"""
    permission_classes = [IsAuthenticated]

    def get_tenant(self):
        try:
            return Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            return None

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas gerais do dashboard"""
        tenant = self.get_tenant()
        if not tenant:
            return Response({'error': 'Tenant não encontrado'}, status=404)

        today = timezone.now().date()

        # Estatísticas básicas
        total_times = Time.objects.filter(tenant=tenant).count()
        total_jogadores = Jogador.objects.filter(tenant=tenant).count()
        total_campeonatos = Campeonato.objects.filter(tenant=tenant).count()

        # Campeonatos ativos
        campeonatos_ativos = Campeonato.objects.filter(
            tenant=tenant,
            data_inicio__lte=today
        ).filter(
            Q(data_fim__isnull=True) | Q(data_fim__gte=today)
        ).count()

        # Partidas hoje
        partidas_hoje = Partida.objects.filter(
            rodada__campeonato__tenant=tenant,
            data_hora__date=today
        ).count()

        # Próximas partidas (próximos 7 dias)
        proximas_partidas = Partida.objects.filter(
            rodada__campeonato__tenant=tenant,
            data_hora__date__gt=today,
            data_hora__date__lte=today + timedelta(days=7),
            encerrada=False
        ).order_by('data_hora')[:5]

        proximas_partidas_data = []
        for partida in proximas_partidas:
            proximas_partidas_data.append({
                'id': partida.id,
                'time_mandante': partida.time_mandante.time.nome,
                'time_visitante': partida.time_visitante.time.nome,
                'data_hora': partida.data_hora,
                'local': partida.local,
                'campeonato': partida.rodada.campeonato.nome
            })

        stats = {
            'total_times': total_times,
            'total_jogadores': total_jogadores,
            'total_campeonatos': total_campeonatos,
            'campeonatos_ativos': campeonatos_ativos,
            'partidas_hoje': partidas_hoje,
            'proximas_partidas': proximas_partidas_data
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


class GolViewSet(viewsets.ModelViewSet):
    """ViewSet para Gols"""
    queryset = Gol.objects.all().order_by('id')
    serializer_class = GolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = None
        try:
            tenant = Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            pass

        if tenant:
            return self.queryset.filter(partida__rodada__campeonato__tenant=tenant).order_by('id')
        return self.queryset.none()
    
    def perform_create(self, serializer):
        gol = serializer.save()
        # Atualizar o placar da partida
        partida = gol.partida
        gols_mandante = Gol.objects.filter(partida=partida, time=partida.time_mandante).count()
        gols_visitante = Gol.objects.filter(partida=partida, time=partida.time_visitante).count()
        partida.placar_mandante = gols_mandante
        partida.placar_visitante = gols_visitante
        partida.save()


class CartaoViewSet(viewsets.ModelViewSet):
    """ViewSet para Cartões"""
    queryset = Cartao.objects.all().order_by('id')
    serializer_class = CartaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = None
        try:
            tenant = Tenant.objects.get(usuario=self.request.user)
        except Tenant.DoesNotExist:
            pass

        if tenant:
            return self.queryset.filter(partida__rodada__campeonato__tenant=tenant).order_by('id')
        return self.queryset.none()


class AuthViewSet(viewsets.ViewSet):
    """ViewSet para autenticação e perfil do usuário"""
    permission_classes = []  # Permitir acesso sem autenticação para login

    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        """Login personalizado que retorna o token JWT e dados do usuário"""
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import authenticate
        from adminpanel.serializers import UsuarioSerializer

        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Username e password são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)

            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UsuarioSerializer(user).data
            })
        else:
            return Response(
                {'detail': 'Credenciais inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout do usuário"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': 'Logout realizado com sucesso'})
        except Exception:
            return Response({'detail': 'Logout realizado com sucesso'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Retorna os dados do perfil do usuário autenticado"""
        from adminpanel.serializers import UsuarioSerializer
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Atualiza os dados do perfil do usuário"""
        from adminpanel.serializers import UsuarioSerializer
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Altera a senha do usuário"""
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'detail': 'old_password e new_password são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(old_password):
            return Response(
                {'detail': 'Senha atual incorreta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response({'detail': 'Senha alterada com sucesso'})
