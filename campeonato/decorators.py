"""
Decoradores personalizados para controle de acesso considerando superusers
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .planos import usuario_tem_plano_ativo

def plano_ativo_required(view_func):
    """
    Decorator que requer plano ativo, exceto para superusers.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Superusers sempre têm acesso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Verificar plano ativo para usuários comuns
        if not usuario_tem_plano_ativo(request.user):
            messages.warning(request, 'É necessário ter um plano ativo para acessar esta funcionalidade.')
            return redirect('campeonato:configuracoes')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view
