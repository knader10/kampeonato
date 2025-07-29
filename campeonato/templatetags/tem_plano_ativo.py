from django import template
from campeonato.planos import usuario_tem_plano_ativo

register = template.Library()

@register.simple_tag(takes_context=True)
def tem_plano_ativo(context):
    user = context['user']
    return usuario_tem_plano_ativo(user)
