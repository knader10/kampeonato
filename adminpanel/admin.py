from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Tenant


class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'nome', 'is_staff', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('nome',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('nome',)}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'password1', 'password2'),
        }),
    )


class TenantAdmin(admin.ModelAdmin):
    list_display = ('nome', 'subdominio', 'usuario', 'status', 'criado_em')
    list_filter = ('status',)
    search_fields = ('nome', 'subdominio')


admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Tenant, TenantAdmin)
