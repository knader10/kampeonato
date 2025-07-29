from django.core.management.base import BaseCommand
from adminpanel.models import Usuario, Tenant
from django.db.models import Count
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Verifica quais usuários não estão associados a um tenant'

    def handle(self, *args, **kwargs):
        Usuario = get_user_model()
        
        # Todos os usuários
        all_users = Usuario.objects.all()
        self.stdout.write(f"Total de usuários: {all_users.count()}")
        
        # Usuários associados a algum tenant
        users_with_tenant = Usuario.objects.filter(
            id__in=Tenant.objects.values_list('usuario_id', flat=True)
        )
        self.stdout.write(f"Usuários com tenant: {users_with_tenant.count()}")
        
        # Usuários não associados a nenhum tenant
        users_without_tenant = Usuario.objects.exclude(
            id__in=Tenant.objects.values_list('usuario_id', flat=True)
        )
        self.stdout.write(f"Usuários sem tenant: {users_without_tenant.count()}")
        
        # Lista os usuários sem tenant
        if users_without_tenant.exists():
            self.stdout.write("\nUsuários sem tenant:")
            for user in users_without_tenant:
                self.stdout.write(f" - {user.nome} (CPF: {user.cpf}, Email: {user.email})")
            
            # Se o usuário quiser associar um tenant ao primeiro usuário sem tenant
            self.stdout.write("\nPara associar um usuário a um tenant, use o comando:")
            self.stdout.write("python manage.py shell")
            self.stdout.write(">>> from adminpanel.models import Usuario, Tenant")
            self.stdout.write(">>> usuario = Usuario.objects.get(cpf='CPF_DO_USUARIO')")
            self.stdout.write(">>> tenant = Tenant.objects.create(nome='Nome do Tenant', subdominio='subdominio', usuario=usuario)")
            self.stdout.write(">>> tenant.save()")
        else:
            self.stdout.write("\nTodos os usuários estão associados a um tenant.")
