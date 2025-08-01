from django import template
from campeonato.planos import usuario_tem_plano_ativo

register = template.Library()

@register.simple_tag(takes_context=True)
def tem_plano_ativo(context):
    user = context['user']
    # Superusers sempre têm acesso
    if user.is_superuser:
        return True
    return usuario_tem_plano_ativo(user)
