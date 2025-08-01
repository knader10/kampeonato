# Generated by Django 5.2.4 on 2025-07-23 20:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campeonato', '0005_alter_rodada_options_rodada_nome'),
    ]

    operations = [
        migrations.CreateModel(
            name='MidiaImagem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.ImageField(upload_to='midia/')),
                ('data_upload', models.DateTimeField(auto_now_add=True)),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='midias', to='campeonato.campeonato')),
            ],
        ),
        migrations.CreateModel(
            name='Noticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('subtitulo', models.CharField(blank=True, max_length=300, null=True)),
                ('descricao', models.TextField()),
                ('ultima_atualizacao', models.DateTimeField(auto_now=True)),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='noticias', to='campeonato.campeonato')),
            ],
        ),
        migrations.CreateModel(
            name='ImagemNoticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.ImageField(upload_to='noticias/')),
                ('noticia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagens', to='campeonato.noticia')),
            ],
        ),
        migrations.CreateModel(
            name='Patrocinio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.ImageField(upload_to='patrocinios/')),
                ('nome', models.CharField(blank=True, max_length=100, null=True)),
                ('data_upload', models.DateTimeField(auto_now_add=True)),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patrocinios', to='campeonato.campeonato')),
            ],
        ),
    ]
