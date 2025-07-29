# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campeonato', '0012_campeonato_disputa_terceiro'),
    ]

    operations = [
        migrations.AddField(
            model_name='partida',
            name='status',
            field=models.CharField(choices=[('nao_iniciada', 'Não Iniciada'), ('em_andamento', 'Em Andamento'), ('finalizada', 'Finalizada')], default='nao_iniciada', max_length=20),
        ),
    ]
