from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Usuario, Tenant

@receiver(post_save, sender=Usuario)
def criar_tenant_automatico(sender, instance, created, **kwargs):
    if created:
        if not Tenant.objects.filter(usuario=instance).exists():
            email = instance.email
            subdominio = slugify(email.split('@')[0])
            nome_organizacao = email
            if Tenant.objects.filter(subdominio=subdominio).exists():
                subdominio = f"{subdominio}-{instance.id}"
            Tenant.objects.create(
                usuario=instance,
                nome=nome_organizacao,
                subdominio=subdominio
            )
