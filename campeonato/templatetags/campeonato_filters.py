# Template filters personalizados para o sistema de campeonatos

from django import template

register = template.Library()

@register.filter
def make_list(value):
    """Converte uma string em lista de caracteres"""
    return list(str(value))

@register.filter
def get_tipo_formato_display(campeonato):
    """Retorna o nome formatado do tipo de formato"""
    return campeonato.get_tipo_formato_display()
