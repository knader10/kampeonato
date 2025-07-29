"""
Template tags personalizados para o sistema de planos
"""
import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def jsonify(value):
    """
    Converte um valor Python para JSON seguro para uso em templates
    """
    return json.dumps(value, cls=DjangoJSONEncoder)
