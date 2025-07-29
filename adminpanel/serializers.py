from rest_framework import serializers
from .models import Usuario, Tenant


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Usuario"""
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'cpf', 'nome', 'email', 'is_active', 'is_staff', 
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class TenantSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Tenant"""
    usuario = UsuarioSerializer(read_only=True)
    
    class Meta:
        model = Tenant
        fields = ['id', 'nome', 'subdominio', 'usuario', 'status', 'criado_em']
        read_only_fields = ['id', 'criado_em']
