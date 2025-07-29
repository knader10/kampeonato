from django.db import models
from django.conf import settings

class Assinatura(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('cancelado', 'Cancelado'),
        ('expirado', 'Expirado'),
        ('pendente', 'Pendente'),
    ]
    PERIODICIDADE_CHOICES = [
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assinaturas')
    plano_id = models.CharField(max_length=30)  # Ex: 'basico', 'pro', 'premium', 'personalizado'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_inicio = models.DateField(auto_now_add=True)
    validade = models.DateField()
    periodicidade = models.CharField(max_length=20, choices=PERIODICIDADE_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def esta_ativa(self):
        from datetime import date
        return self.status == 'ativo' and self.validade >= date.today()

    def __str__(self):
        return f"{self.user} - {self.plano_id} ({self.status})"
