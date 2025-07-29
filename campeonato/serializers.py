from rest_framework import serializers
from .models import (
    Time, Jogador, Profissional, Campeonato, TimeCampeonato, 
    JogadorTimeCampeonato, ProfissionalCampeonato, Rodada, 
    Partida, ProfissionalPartida, Gol, Cartao, Despesa
)
from adminpanel.models import Tenant


class TimeSerializer(serializers.ModelSerializer):
    escudo_url = serializers.SerializerMethodField()
    total_jogadores = serializers.SerializerMethodField()
    
    class Meta:
        model = Time
        fields = ['id', 'nome', 'escudo', 'escudo_url', 'ano_fundacao', 'cidade', 'total_jogadores']
        
    def get_escudo_url(self, obj):
        if obj.escudo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.escudo.url)
        return None
        
    def get_total_jogadores(self, obj):
        # Busca todos os vínculos JogadorTimeCampeonato ativos para este time em todos os campeonatos
        from .models import JogadorTimeCampeonato
        return JogadorTimeCampeonato.objects.filter(
            time_campeonato__time=obj,
            ativo=True
        ).count()


class JogadorSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()
    idade = serializers.SerializerMethodField()
    times_atuais = serializers.SerializerMethodField()
    
    class Meta:
        model = Jogador
        fields = [
            'id', 'nome', 'foto', 'foto_url', 'data_nascimento', 'idade',
            'cidade', 'logradouro', 'cep', 'bairro', 'complemento',
            'titulo_eleitor', 'zona_eleitoral', 'secao_eleitoral', 
            'telefone', 'times_atuais'
        ]
        
    def get_foto_url(self, obj):
        if obj.foto:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto.url)
        return None
        
    def get_idade(self, obj):
        from datetime import date
        if obj.data_nascimento:
            today = date.today()
            return today.year - obj.data_nascimento.year - (
                (today.month, today.day) < (obj.data_nascimento.month, obj.data_nascimento.day)
            )
        return None
        
    def get_times_atuais(self, obj):
        vinculos_ativos = obj.historico.filter(ativo=True)
        return [
            {
                'time_nome': vinculo.time_campeonato.time.nome,
                'campeonato_nome': vinculo.time_campeonato.campeonato.nome,
                'data_entrada': vinculo.data_entrada
            }
            for vinculo in vinculos_ativos
        ]


class ProfissionalSerializer(serializers.ModelSerializer):
    campeonatos_atuais = serializers.SerializerMethodField()

    class Meta:
        model = Profissional
        fields = [
            'id', 'nome', 'cpf', 'cidade', 'federacao', 'liga',
            'telefone', 'chave_pix', 'tipo_chave_pix', 'campeonatos_atuais'
        ]
        extra_kwargs = {
            'cpf': {'required': False, 'allow_null': True, 'allow_blank': True},
            'cidade': {'required': False, 'allow_null': True, 'allow_blank': True},
            'federacao': {'required': False, 'allow_null': True, 'allow_blank': True},
            'liga': {'required': False, 'allow_null': True, 'allow_blank': True},
            'telefone': {'required': False, 'allow_null': True, 'allow_blank': True},
            'chave_pix': {'required': False, 'allow_null': True, 'allow_blank': True},
            'tipo_chave_pix': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
        
    def get_campeonatos_atuais(self, obj):
        return [
            {
                'campeonato_nome': atuacao.campeonato.nome,
                'campeonato_edicao': atuacao.campeonato.edicao
            }
            for atuacao in obj.atuacoes.all()
        ]


class CampeonatoSerializer(serializers.ModelSerializer):
    total_times = serializers.SerializerMethodField()
    total_profissionais = serializers.SerializerMethodField()
    profissionais = serializers.SerializerMethodField()  # NOVO

    class Meta:
        model = Campeonato
        fields = [
            'id', 'nome', 'edicao', 'organizador', 'data_inicio',
            'data_fim', 'permite_transferencia', 'total_times',
            'total_profissionais', 'status',
            'tipo_formato', 'ida_volta', 'num_turnos', 'num_divisoes',
            'num_grupos', 'num_classificados', 'observacoes_formato',
            'disputa_terceiro', 'confrontos_mesmo_grupo',  # Novo campo
            'profissionais'  # NOVO
        ]
        
    def get_total_times(self, obj):
        return obj.times.count()
        
    def get_total_profissionais(self, obj):
        return obj.profissionais.count()

    def get_profissionais(self, obj):
        profissionais_vinculados = obj.profissionais.all()
        return ProfissionalCampeonatoSerializer(profissionais_vinculados, many=True).data


class TimeCampeonatoSerializer(serializers.ModelSerializer):
    time = TimeSerializer(read_only=True)
    time_id = serializers.IntegerField(write_only=True)
    total_jogadores = serializers.SerializerMethodField()
    jogadores = serializers.SerializerMethodField()
    
    class Meta:
        model = TimeCampeonato
        fields = [
            'id', 'time', 'time_id', 'campeonato', 'data_inscricao',
            'localizacao', 'campo_estadio', 'presidente', 
            'total_jogadores', 'jogadores'
        ]
        
    def get_total_jogadores(self, obj):
        return obj.jogadores.filter(ativo=True).count()
        
    def get_jogadores(self, obj):
        jogadores_ativos = obj.jogadores.filter(ativo=True)
        return JogadorTimeCampeonatoSerializer(jogadores_ativos, many=True).data


class JogadorTimeCampeonatoSerializer(serializers.ModelSerializer):
    jogador = JogadorSerializer(read_only=True)
    jogador_id = serializers.IntegerField(write_only=True)
    time_campeonato_info = serializers.SerializerMethodField()
    
    class Meta:
        model = JogadorTimeCampeonato
        fields = [
            'id', 'jogador', 'jogador_id', 'time_campeonato', 
            'data_entrada', 'data_saida', 'ativo', 'time_campeonato_info'
        ]
        
    def get_time_campeonato_info(self, obj):
        return {
            'time_nome': obj.time_campeonato.time.nome,
            'campeonato_nome': obj.time_campeonato.campeonato.nome
        }


class ProfissionalCampeonatoSerializer(serializers.ModelSerializer):
    profissional = ProfissionalSerializer(read_only=True)
    profissional_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProfissionalCampeonato
        fields = ['id', 'profissional', 'profissional_id', 'campeonato']


class RodadaSerializer(serializers.ModelSerializer):
    total_partidas = serializers.SerializerMethodField()
    partidas_encerradas = serializers.SerializerMethodField()
    
    class Meta:
        model = Rodada
        fields = [
            'id', 'campeonato', 'numero', 'data', 'observacoes',
            'total_partidas', 'partidas_encerradas'
        ]
        
    def get_total_partidas(self, obj):
        return obj.partidas.count()
        
    def get_partidas_encerradas(self, obj):
        return obj.partidas.filter(encerrada=True).count()


class PartidaSerializer(serializers.ModelSerializer):
    time_mandante_info = serializers.SerializerMethodField()
    time_visitante_info = serializers.SerializerMethodField()
    total_gols = serializers.SerializerMethodField()
    total_cartoes = serializers.SerializerMethodField()
    resultado = serializers.SerializerMethodField()
    rodada_nome = serializers.SerializerMethodField()
    
    class Meta:
        model = Partida
        fields = [
            'id', 'rodada', 'rodada_nome', 'time_mandante', 'time_visitante',
            'time_mandante_info', 'time_visitante_info',
            'data_hora', 'local', 'placar_mandante', 'placar_visitante',
            'status', 'encerrada', 'observacoes', 'total_gols', 'total_cartoes',        'resultado'
        ]
    
    def get_time_mandante_info(self, obj):
        if not obj.time_mandante:
            return None
            
        escudo_url = None
        if obj.time_mandante.time.escudo:
            request = self.context.get('request')
            if request:
                escudo_url = request.build_absolute_uri(obj.time_mandante.time.escudo.url)
            else:
                escudo_url = obj.time_mandante.time.escudo.url
                
        return {
            'id': obj.time_mandante.id,
            'nome': obj.time_mandante.time.nome,
            'cidade': obj.time_mandante.time.cidade,
            'escudo_url': escudo_url
        }
        
    def get_time_visitante_info(self, obj):
        if not obj.time_visitante:
            return None
            
        escudo_url = None
        if obj.time_visitante.time.escudo:
            request = self.context.get('request')
            if request:
                escudo_url = request.build_absolute_uri(obj.time_visitante.time.escudo.url)
            else:
                escudo_url = obj.time_visitante.time.escudo.url
                
        return {
            'id': obj.time_visitante.id,
            'nome': obj.time_visitante.time.nome,
            'cidade': obj.time_visitante.time.cidade,
            'escudo_url': escudo_url
        }
        
    def get_total_gols(self, obj):
        return obj.gols.count()
        
    def get_total_cartoes(self, obj):
        return obj.cartoes.count()
        
    def get_resultado(self, obj):
        if not obj.encerrada:
            return None
        
        if obj.placar_mandante > obj.placar_visitante:
            return 'vitoria_mandante'
        elif obj.placar_visitante > obj.placar_mandante:
            return 'vitoria_visitante'
        else:
            return 'empate'

    def get_rodada_nome(self, obj):
        if obj.rodada.observacoes:
            return obj.rodada.observacoes
        return f'Rodada {obj.rodada.numero}'


class GolSerializer(serializers.ModelSerializer):
    jogador_info = serializers.SerializerMethodField()
    time_info = serializers.SerializerMethodField()
    jogador_id = serializers.SerializerMethodField()  # ID do Jogador (não JogadorTimeCampeonato)
    time_id = serializers.SerializerMethodField()     # ID do TimeCampeonato
    
    class Meta:
        model = Gol
        fields = [
            'id', 'partida', 'jogador', 'jogador_info', 'jogador_id',
            'time', 'time_info', 'time_id', 'minuto', 'tipo'
        ]
        
    def get_jogador_info(self, obj):
        return {
            'nome': obj.jogador.jogador.nome,
            'foto_url': obj.jogador.jogador.foto.url if obj.jogador.jogador.foto else None
        }
        
    def get_time_info(self, obj):
        return {
            'nome': obj.time.time.nome,
            'escudo_url': obj.time.time.escudo.url if obj.time.time.escudo else None
        }
    
    def get_jogador_id(self, obj):
        # Retorna o ID do Jogador (não do JogadorTimeCampeonato)
        return obj.jogador.jogador.id
    
    def get_time_id(self, obj):
        # Retorna o ID do TimeCampeonato
        return obj.time.id


class CartaoSerializer(serializers.ModelSerializer):
    jogador_info = serializers.SerializerMethodField()
    jogador_id = serializers.SerializerMethodField()
    time_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Cartao
        fields = [
            'id', 'partida', 'jogador', 'jogador_info', 'jogador_id', 'time_id',
            'tipo', 'minuto', 'motivo'
        ]
        
    def get_jogador_info(self, obj):
        return {
            'nome': obj.jogador.jogador.nome,
            'time_nome': obj.jogador.time_campeonato.time.nome
        }
    
    def get_jogador_id(self, obj):
        # Retorna o ID do Jogador (não do JogadorTimeCampeonato)
        return obj.jogador.jogador.id
    
    def get_time_id(self, obj):
        # Retorna o ID do TimeCampeonato
        return obj.jogador.time_campeonato.id


class ProfissionalPartidaSerializer(serializers.ModelSerializer):
    profissional_campeonato = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfissionalPartida
        fields = [
            'id', 'profissional_campeonato', 'partida', 'funcao', 'valor', 'descricao'
        ]
        
    def get_profissional_campeonato(self, obj):
        """Retorna dados completos do vínculo ProfissionalCampeonato"""
        return {
            'id': obj.profissional_campeonato.id,
            'profissional': {
                'id': obj.profissional_campeonato.profissional.id,
                'nome': obj.profissional_campeonato.profissional.nome,
                'federacao': obj.profissional_campeonato.profissional.federacao,
            }
        }


class DespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despesa
        fields = ['id', 'profissional_partida', 'descricao', 'valor']


# Serializers específicos para estatísticas e dashboards
class EstatisticasTimeSerializer(serializers.Serializer):
    time_id = serializers.IntegerField()
    time_nome = serializers.CharField()
    jogos = serializers.IntegerField()
    vitorias = serializers.IntegerField()
    empates = serializers.IntegerField()
    derrotas = serializers.IntegerField()
    gols_pro = serializers.IntegerField()
    gols_contra = serializers.IntegerField()
    saldo_gols = serializers.IntegerField()
    pontos = serializers.IntegerField()
    aproveitamento = serializers.FloatField()


class ArtilheiroSerializer(serializers.Serializer):
    jogador_id = serializers.IntegerField()
    jogador_nome = serializers.CharField()
    time_nome = serializers.CharField()
    total_gols = serializers.IntegerField()
    gols_normais = serializers.IntegerField()
    gols_penalti = serializers.IntegerField()
    gols_contra = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    total_times = serializers.IntegerField()
    total_jogadores = serializers.IntegerField()
    total_campeonatos = serializers.IntegerField()
    campeonatos_ativos = serializers.IntegerField()
    partidas_hoje = serializers.IntegerField()
    proximas_partidas = serializers.ListField()
