# Generated by Django 5.2.4 on 2025-07-09 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campeonato', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campeonato',
            name='num_classificados',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='campeonato',
            name='num_grupos',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
