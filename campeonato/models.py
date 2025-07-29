from django.db import models
from adminpanel.models import Usuario, Tenant


# Modelos básicos

class Time(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='times')
    nome = models.CharField(max_length=100)
    escudo = models.ImageField(upload_to='escudos/', blank=True, null=True)
    ano_fundacao = models.IntegerField()
    cidade = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Time'
        verbose_name_plural = 'Times'


class Jogador(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='jogadores')
    nome = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='jogadores/', blank=True, null=True)
    data_nascimento = models.DateField()
    
    # Endereço
    cidade = models.CharField(max_length=100)
    logradouro = models.CharField(max_length=200)
    cep = models.CharField(max_length=9)
    bairro = models.CharField(max_length=100)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    
    # Informações eleitorais
    titulo_eleitor = models.CharField(max_length=12, blank=True, null=True)
    zona_eleitoral = models.CharField(max_length=4, blank=True, null=True)
    secao_eleitoral = models.CharField(max_length=4, blank=True, null=True)
    
    telefone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    @property
    def idade(self):
        """Calcula a idade do jogador baseada na data de nascimento"""
        if self.data_nascimento:
            from datetime import date
            hoje = date.today()
            return hoje.year - self.data_nascimento.year - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
        return None
    
    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'


class Profissional(models.Model):
    TIPOS_CHAVE_PIX = [
        ('EMAIL', 'E-mail'),
        ('TELEFONE', 'Telefone'),
        ('CPF', 'CPF'),
        ('ALEATORIA', 'Aleatória'),
        ('OUTRA', 'Outra'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='profissionais')
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    cidade = models.CharField(max_length=100)
    federacao = models.CharField(max_length=100)
    liga = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    chave_pix = models.CharField(max_length=200, blank=True, null=True)
    tipo_chave_pix = models.CharField(max_length=10, choices=TIPOS_CHAVE_PIX, blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'


class Campeonato(models.Model):
    STATUS_CHOICES = [
        ('nao_iniciado', 'Não iniciado'),
        ('em_andamento', 'Em andamento'),
        ('finalizado', 'Finalizado'),
    ]
    FORMATO_CHOICES = [
        ('liga', 'Liga'),
        ('mata_mata', 'Mata-mata'),
        ('misto', 'Misto'),

    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='campeonatos')
    nome = models.CharField(max_length=100)
    edicao = models.CharField(max_length=50)
    organizador = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    permite_transferencia = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='nao_iniciado')
    codigo_publico = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Para URLs públicas
    # Novos campos de formato
    tipo_formato = models.CharField(max_length=20, choices=FORMATO_CHOICES, default='liga')
    ida_volta = models.BooleanField(default=False)
    num_turnos = models.PositiveIntegerField(default=1)
    num_divisoes = models.PositiveIntegerField(default=0, blank=True, null=True)
    num_grupos = models.PositiveIntegerField(default=0, blank=True, null=True)
    num_classificados = models.PositiveIntegerField(default=0, blank=True, null=True)
    observacoes_formato = models.TextField(blank=True, null=True)
    disputa_terceiro = models.BooleanField(default=False)
    confrontos_mesmo_grupo = models.BooleanField(default=True)  # Novo campo
    
    def save(self, *args, **kwargs):
        if not self.codigo_publico:
            self.codigo_publico = self._gerar_codigo_publico()
        # Atualizar status automaticamente baseado nas datas
        self._atualizar_status_automatico()
        super().save(*args, **kwargs)
    
    def _atualizar_status_automatico(self):
        """Atualiza o status automaticamente baseado nas datas"""
        from datetime import date
        hoje = date.today()
        
        # Se já está marcado como finalizado manualmente, não alterar
        if self.status == 'finalizado':
            return
        
        # Se tem data de fim e já passou, marcar como finalizado
        if self.data_fim and hoje > self.data_fim:
            self.status = 'finalizado'
        # Se já começou mas não terminou (ou não tem data fim), marcar como em andamento
        elif hoje >= self.data_inicio:
            if not self.data_fim or hoje <= self.data_fim:
                self.status = 'em_andamento'
        # Se ainda não começou, marcar como não iniciado
        else:
            self.status = 'nao_iniciado'
    
    @property
    def status_automatico(self):
        """Retorna o status que deveria ter baseado nas datas"""
        from datetime import date
        hoje = date.today()
        
        if self.data_fim and hoje > self.data_fim:
            return 'finalizado'
        elif hoje >= self.data_inicio:
            if not self.data_fim or hoje <= self.data_fim:
                return 'em_andamento'
        else:
            return 'nao_iniciado'
    
    def _gerar_codigo_publico(self):
        """Gera um código público único para o campeonato"""
        import secrets
        import string
        
        # Primeiro tenta usar uma combinação do nome + ano
        nome_limpo = ''.join(c for c in self.nome.lower() if c.isalnum())[:8]
        ano = str(self.data_inicio.year)
        
        codigo_base = f"{nome_limpo}{ano}"
        
        # Se o código base já existe, adiciona sufixo aleatório
        codigo = codigo_base
        contador = 1
        while Campeonato.objects.filter(codigo_publico=codigo).exists():
            if contador == 1:
                # Adiciona 3 caracteres aleatórios
                sufixo = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(3))
                codigo = f"{codigo_base}{sufixo}"
            else:
                # Se ainda existe, gera código totalmente aleatório
                codigo = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
            contador += 1
            
        return codigo[:20]  # Limita a 20 caracteres
    
    @property
    def esta_ativo(self):
        """Verifica se o campeonato está ativo"""
        from datetime import date
        hoje = date.today()
        if self.data_fim:
            return self.data_inicio <= hoje <= self.data_fim
        return self.data_inicio <= hoje
    
    @property
    def numero_grupos(self):
        """Retorna o número de grupos (compatibilidade)"""
        return self.num_grupos
    
    @property
    def numero_classificados(self):
        """Retorna o número de classificados (compatibilidade)"""
        return self.num_classificados
    
    @property 
    def observacoes(self):
        """Retorna as observações do formato (compatibilidade)"""
        return self.observacoes_formato
    
    def get_formato_display(self):
        """Retorna o nome do formato para exibição"""
        return dict(self.FORMATO_CHOICES).get(self.tipo_formato, self.tipo_formato)
    
    def __str__(self):
        return f"{self.nome} - {self.edicao}"
    
    class Meta:
        verbose_name = 'Campeonato'
        verbose_name_plural = 'Campeonatos'


# Relacionamentos

class TimeCampeonato(models.Model):
    time = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='participacoes')
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='times')
    data_inscricao = models.DateField(auto_now_add=True)
    
    # Informações específicas do time neste campeonato
    localizacao = models.CharField(max_length=200, blank=True, null=True)
    campo_estadio = models.CharField(max_length=200, blank=True, null=True)
    presidente = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.time.nome} - {self.campeonato.nome}"
    
    @property
    def jogadores_ativos_count(self):
        """Retorna o número de jogadores ativos vinculados a este time no campeonato"""
        return self.jogadores.filter(ativo=True).count()
    
    @property
    def jogadores_ativos(self):
        """Retorna os jogadores ativos vinculados a este time no campeonato"""
        return self.jogadores.filter(ativo=True)
    
    class Meta:
        verbose_name = 'Participação de Time'
        verbose_name_plural = 'Participações de Times'
        unique_together = ['time', 'campeonato']


class JogadorTimeCampeonato(models.Model):
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='historico')
    time_campeonato = models.ForeignKey(TimeCampeonato, on_delete=models.CASCADE, related_name='jogadores')
    data_entrada = models.DateField(auto_now_add=True)
    data_saida = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.jogador.nome} - {self.time_campeonato.time.nome} ({self.time_campeonato.campeonato.nome})"
    
    class Meta:
        verbose_name = 'Vínculo Jogador-Time-Campeonato'
        verbose_name_plural = 'Vínculos Jogador-Time-Campeonato'


class ProfissionalCampeonato(models.Model):
    FUNCOES = [
        ('ARB', 'Árbitro'),
        ('BAN', 'Bandeirinha'),
        ('MES', 'Mesário'),
        ('QAR', 'Quarto Árbitro'),
        ('OUT', 'Outras funções'),
    ]
    
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='atuacoes')
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='profissionais')
    funcao = models.CharField(max_length=100, blank=True, null=True)
    data_vinculacao = models.DateField(auto_now_add=True, null=True)
    
    def __str__(self):
        return f"{self.profissional.nome} - {self.campeonato.nome}"
    
    class Meta:
        verbose_name = 'Profissional no Campeonato'
        verbose_name_plural = 'Profissionais nos Campeonatos'
        unique_together = ['profissional', 'campeonato']


# Modelos para partidas e estatísticas

class Rodada(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='rodadas')
    numero = models.IntegerField()
    nome = models.CharField(max_length=100, blank=True, null=True)  # Nome personalizado da rodada
    data = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    
    def get_nome_exibicao(self):
        """Retorna o nome da rodada baseado no formato do campeonato"""
        if self.nome:
            return self.nome
        
        if self.campeonato.tipo_formato == 'liga':
            total_times = self.campeonato.times.count()
            if self.campeonato.ida_volta:
                if self.numero <= total_times - 1:
                    return f"Round {self.numero}"  # Internationalization ready
                else:
                    return f"Round {self.numero} - Return"
            else:
                return f"Round {self.numero}"
        elif self.campeonato.tipo_formato == 'mata_mata':
            # Para mata-mata, calcular a fase baseada no número de times
            total_times = self.campeonato.times.count()
            if total_times <= 2:
                return "Final"
            elif total_times <= 4:
                return "Semifinal" if self.numero <= 2 else "Final"
            elif total_times <= 8:
                if self.numero <= 4:
                    return "Quarterfinal"
                elif self.numero <= 6:
                    return "Semifinal"
                else:
                    return "Final"
            else:
                return f"Round {self.numero}"
        else:
            return f"Round {self.numero}"
    
    @property
    def is_turno(self):
        """Verifica se é uma rodada de turno (ida)"""
        if not self.campeonato.ida_volta:
            return True
        total_times = self.campeonato.times.count()
        return self.numero <= total_times - 1
    
    @property
    def is_returno(self):
        """Verifica se é uma rodada de returno (volta)"""
        if not self.campeonato.ida_volta:
            return False
        total_times = self.campeonato.times.count()
        return self.numero > total_times - 1
    
    def __str__(self):
        return f"{self.get_nome_exibicao()} - {self.campeonato.nome}"
    
    class Meta:
        verbose_name = 'Rodada'
        verbose_name_plural = 'Rodadas'
        unique_together = ['campeonato', 'numero']
        ordering = ['numero']


class Partida(models.Model):
    STATUS_CHOICES = [
        ('nao_iniciada', 'Não Iniciada'),
        ('em_andamento', 'Em Andamento'),
        ('finalizada', 'Finalizada'),
    ]
    
    rodada = models.ForeignKey(Rodada, on_delete=models.CASCADE, related_name='partidas')
    time_mandante = models.ForeignKey(TimeCampeonato, on_delete=models.CASCADE, related_name='partidas_como_mandante', null=True, blank=True)
    time_visitante = models.ForeignKey(TimeCampeonato, on_delete=models.CASCADE, related_name='partidas_como_visitante', null=True, blank=True)
    data_hora = models.DateTimeField(null=True, blank=True)
    local = models.CharField(max_length=100, blank=True)
    placar_mandante = models.IntegerField(default=0)
    placar_visitante = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nao_iniciada')
    encerrada = models.BooleanField(default=False)  # Manter para compatibilidade
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.time_mandante and self.time_visitante:
            return f"{self.time_mandante.time.nome} {self.placar_mandante} x {self.placar_visitante} {self.time_visitante.time.nome}"
        elif self.observacoes:
            return f"Partida: {self.observacoes}"
        else:
            return f"Partida {self.id} (times a definir)"
    
    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'


class ProfissionalPartida(models.Model):
    FUNCOES = [
        ('ARB', 'Árbitro'),
        ('BAN', 'Bandeirinha'),
        ('MES', 'Mesário'),
        ('QAR', 'Quarto Árbitro'),
    ]
    
    profissional_campeonato = models.ForeignKey(ProfissionalCampeonato, on_delete=models.CASCADE, related_name='partidas')
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='profissionais')
    funcao = models.CharField(max_length=3, choices=FUNCOES)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.profissional_campeonato.profissional.nome} - {self.get_funcao_display()} - {self.partida}"
    
    class Meta:
        verbose_name = 'Profissional na Partida'
        verbose_name_plural = 'Profissionais nas Partidas'


class Gol(models.Model):
    TIPOS = [
        ('NOR', 'Normal'),
        ('PEN', 'Pênalti'),
        ('CON', 'Contra'),
    ]
    
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='gols')
    jogador = models.ForeignKey(JogadorTimeCampeonato, on_delete=models.CASCADE, related_name='gols')
    time = models.ForeignKey(TimeCampeonato, on_delete=models.CASCADE, related_name='gols')
    minuto = models.IntegerField()
    tipo = models.CharField(max_length=3, choices=TIPOS, default='NOR')
    
    def __str__(self):
        return f"{self.jogador.jogador.nome} - {self.partida} - {self.minuto}'"
    
    class Meta:
        verbose_name = 'Gol'
        verbose_name_plural = 'Gols'


class Cartao(models.Model):
    TIPOS = [
        ('AMA', 'Amarelo'),
        ('VER', 'Vermelho'),
    ]
    
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='cartoes')
    jogador = models.ForeignKey(JogadorTimeCampeonato, on_delete=models.CASCADE, related_name='cartoes')
    tipo = models.CharField(max_length=3, choices=TIPOS)
    minuto = models.IntegerField()
    motivo = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.jogador.jogador.nome} - Cartão {self.get_tipo_display()} - {self.partida}"
    
    class Meta:
        verbose_name = 'Cartão'
        verbose_name_plural = 'Cartões'


class Despesa(models.Model):
    profissional_partida = models.ForeignKey(ProfissionalPartida, on_delete=models.CASCADE, related_name='despesas')
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.descricao} - R${self.valor} - {self.profissional_partida.profissional_campeonato.profissional.nome}"
    
    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'


class Noticia(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='noticias')
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True, null=True)
    descricao = models.TextField()
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    # Não é obrigatório ter imagem

    def __str__(self):
        return self.titulo

class ImagemNoticia(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='noticias/')

class MidiaImagem(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='midias')
    imagem = models.ImageField(upload_to='midia/')
    data_upload = models.DateTimeField(auto_now_add=True)

class Patrocinio(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='patrocinios')
    imagem = models.ImageField(upload_to='patrocinios/')
    nome = models.CharField(max_length=100, blank=True, null=True)
    data_upload = models.DateTimeField(auto_now_add=True)
