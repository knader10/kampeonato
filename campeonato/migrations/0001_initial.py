# Generated by Django 5.2.4 on 2025-07-08 17:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('adminpanel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(blank=True, null=True)),
                ('local', models.CharField(blank=True, max_length=100)),
                ('placar_mandante', models.IntegerField(default=0)),
                ('placar_visitante', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('nao_iniciada', 'Não Iniciada'), ('em_andamento', 'Em Andamento'), ('finalizada', 'Finalizada')], default='nao_iniciada', max_length=20)),
                ('encerrada', models.BooleanField(default=False)),
                ('observacoes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Partida',
                'verbose_name_plural': 'Partidas',
            },
        ),
        migrations.CreateModel(
            name='Campeonato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('edicao', models.CharField(max_length=50)),
                ('organizador', models.CharField(max_length=100)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField(blank=True, null=True)),
                ('permite_transferencia', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('nao_iniciado', 'Não iniciado'), ('em_andamento', 'Em andamento'), ('finalizado', 'Finalizado')], default='nao_iniciado', max_length=15)),
                ('codigo_publico', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('tipo_formato', models.CharField(choices=[('liga', 'Liga'), ('mata_mata', 'Mata-mata'), ('misto', 'Misto')], default='liga', max_length=20)),
                ('ida_volta', models.BooleanField(default=False)),
                ('num_turnos', models.PositiveIntegerField(default=1)),
                ('num_divisoes', models.PositiveIntegerField(default=0)),
                ('num_grupos', models.PositiveIntegerField(default=0)),
                ('num_classificados', models.PositiveIntegerField(default=0)),
                ('observacoes_formato', models.TextField(blank=True, null=True)),
                ('disputa_terceiro', models.BooleanField(default=False)),
                ('confrontos_mesmo_grupo', models.BooleanField(default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campeonatos', to='adminpanel.tenant')),
            ],
            options={
                'verbose_name': 'Campeonato',
                'verbose_name_plural': 'Campeonatos',
            },
        ),
        migrations.CreateModel(
            name='Jogador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='jogadores/')),
                ('data_nascimento', models.DateField()),
                ('cidade', models.CharField(max_length=100)),
                ('logradouro', models.CharField(max_length=200)),
                ('cep', models.CharField(max_length=9)),
                ('bairro', models.CharField(max_length=100)),
                ('complemento', models.CharField(blank=True, max_length=100, null=True)),
                ('titulo_eleitor', models.CharField(blank=True, max_length=12, null=True)),
                ('zona_eleitoral', models.CharField(blank=True, max_length=4, null=True)),
                ('secao_eleitoral', models.CharField(blank=True, max_length=4, null=True)),
                ('telefone', models.CharField(blank=True, max_length=15, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jogadores', to='adminpanel.tenant')),
            ],
            options={
                'verbose_name': 'Jogador',
                'verbose_name_plural': 'Jogadores',
            },
        ),
        migrations.CreateModel(
            name='JogadorTimeCampeonato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_entrada', models.DateField(auto_now_add=True)),
                ('data_saida', models.DateField(blank=True, null=True)),
                ('ativo', models.BooleanField(default=True)),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico', to='campeonato.jogador')),
            ],
            options={
                'verbose_name': 'Vínculo Jogador-Time-Campeonato',
                'verbose_name_plural': 'Vínculos Jogador-Time-Campeonato',
            },
        ),
        migrations.CreateModel(
            name='Cartao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('AMA', 'Amarelo'), ('VER', 'Vermelho')], max_length=3)),
                ('minuto', models.IntegerField()),
                ('motivo', models.CharField(blank=True, max_length=200, null=True)),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cartoes', to='campeonato.jogadortimecampeonato')),
                ('partida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cartoes', to='campeonato.partida')),
            ],
            options={
                'verbose_name': 'Cartão',
                'verbose_name_plural': 'Cartões',
            },
        ),
        migrations.CreateModel(
            name='Profissional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('cpf', models.CharField(blank=True, max_length=14, null=True)),
                ('cidade', models.CharField(max_length=100)),
                ('federacao', models.CharField(max_length=100)),
                ('liga', models.CharField(max_length=100)),
                ('telefone', models.CharField(blank=True, max_length=15, null=True)),
                ('chave_pix', models.CharField(blank=True, max_length=200, null=True)),
                ('tipo_chave_pix', models.CharField(blank=True, choices=[('EMAIL', 'E-mail'), ('TELEFONE', 'Telefone'), ('CPF', 'CPF'), ('ALEATORIA', 'Aleatória'), ('OUTRA', 'Outra')], max_length=10, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profissionais', to='adminpanel.tenant')),
            ],
            options={
                'verbose_name': 'Profissional',
                'verbose_name_plural': 'Profissionais',
            },
        ),
        migrations.CreateModel(
            name='ProfissionalCampeonato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profissionais', to='campeonato.campeonato')),
                ('profissional', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atuacoes', to='campeonato.profissional')),
            ],
            options={
                'verbose_name': 'Profissional no Campeonato',
                'verbose_name_plural': 'Profissionais nos Campeonatos',
                'unique_together': {('profissional', 'campeonato')},
            },
        ),
        migrations.CreateModel(
            name='ProfissionalPartida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('funcao', models.CharField(choices=[('ARB', 'Árbitro'), ('BAN', 'Bandeirinha'), ('MES', 'Mesário'), ('QAR', 'Quarto Árbitro')], max_length=3)),
                ('valor', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('descricao', models.CharField(blank=True, max_length=200, null=True)),
                ('partida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profissionais', to='campeonato.partida')),
                ('profissional_campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partidas', to='campeonato.profissionalcampeonato')),
            ],
            options={
                'verbose_name': 'Profissional na Partida',
                'verbose_name_plural': 'Profissionais nas Partidas',
            },
        ),
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('profissional_partida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='despesas', to='campeonato.profissionalpartida')),
            ],
            options={
                'verbose_name': 'Despesa',
                'verbose_name_plural': 'Despesas',
            },
        ),
        migrations.CreateModel(
            name='Rodada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.IntegerField()),
                ('data', models.DateField()),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rodadas', to='campeonato.campeonato')),
            ],
            options={
                'verbose_name': 'Rodada',
                'verbose_name_plural': 'Rodadas',
                'unique_together': {('campeonato', 'numero')},
            },
        ),
        migrations.AddField(
            model_name='partida',
            name='rodada',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partidas', to='campeonato.rodada'),
        ),
        migrations.CreateModel(
            name='Time',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('escudo', models.ImageField(blank=True, null=True, upload_to='escudos/')),
                ('ano_fundacao', models.IntegerField()),
                ('cidade', models.CharField(max_length=100)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='times', to='adminpanel.tenant')),
            ],
            options={
                'verbose_name': 'Time',
                'verbose_name_plural': 'Times',
            },
        ),
        migrations.CreateModel(
            name='TimeCampeonato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inscricao', models.DateField(auto_now_add=True)),
                ('localizacao', models.CharField(blank=True, max_length=200, null=True)),
                ('campo_estadio', models.CharField(blank=True, max_length=200, null=True)),
                ('presidente', models.CharField(blank=True, max_length=100, null=True)),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='times', to='campeonato.campeonato')),
                ('time', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participacoes', to='campeonato.time')),
            ],
            options={
                'verbose_name': 'Participação de Time',
                'verbose_name_plural': 'Participações de Times',
                'unique_together': {('time', 'campeonato')},
            },
        ),
        migrations.AddField(
            model_name='partida',
            name='time_mandante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='partidas_como_mandante', to='campeonato.timecampeonato'),
        ),
        migrations.AddField(
            model_name='partida',
            name='time_visitante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='partidas_como_visitante', to='campeonato.timecampeonato'),
        ),
        migrations.AddField(
            model_name='jogadortimecampeonato',
            name='time_campeonato',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jogadores', to='campeonato.timecampeonato'),
        ),
        migrations.CreateModel(
            name='Gol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minuto', models.IntegerField()),
                ('tipo', models.CharField(choices=[('NOR', 'Normal'), ('PEN', 'Pênalti'), ('CON', 'Contra')], default='NOR', max_length=3)),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gols', to='campeonato.jogadortimecampeonato')),
                ('partida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gols', to='campeonato.partida')),
                ('time', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gols', to='campeonato.timecampeonato')),
            ],
            options={
                'verbose_name': 'Gol',
                'verbose_name_plural': 'Gols',
            },
        ),
    ]
