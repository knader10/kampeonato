from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from decimal import Decimal
from adminpanel.mercadopago_utils import criar_preferencia_pagamento
from adminpanel.models_assinatura import Assinatura
from campeonato.planos import PlanoManager
import json

@login_required
def checkout_mercadopago(request, plano_id, periodicidade):
    plano_manager = PlanoManager()
    plano = plano_manager.get_plano_by_id(plano_id)
    preco = plano['precos'][periodicidade]
    success_url = request.build_absolute_uri('/assinatura/sucesso/')
    failure_url = request.build_absolute_uri('/assinatura/erro/')
    notification_url = request.build_absolute_uri('/mercadopago/webhook/')
    preference_response = criar_preferencia_pagamento(
        user=request.user,
        plano_id=plano_id,
        periodicidade=periodicidade,
        preco=preco,
        success_url=success_url,
        failure_url=failure_url,
        notification_url=notification_url
    )
    # Debug: exibe resposta completa se não houver init_point
    try:
        link = preference_response["response"]["init_point"]
    except KeyError:
        # Exibe erro detalhado para debug
        return JsonResponse({
            "error": "Campo init_point não encontrado na resposta do Mercado Pago.",
            "api_response": preference_response,
            "dica": "Verifique o MERCADOPAGO_ACCESS_TOKEN, dados do plano e se o ambiente está correto (sandbox/produção)."
        }, status=400)
    except Exception as e:
        return JsonResponse({"erro": "Falha inesperada ao gerar link Mercado Pago", "exception": str(e), "retorno": preference_response}, status=400)
    return redirect(link)

@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    data = json.loads(request.body.decode())
    # Exemplo: processar notificação de pagamento aprovado
    if data.get('type') == 'payment':
        payment_id = data.get('data', {}).get('id')
        # Aqui você pode consultar detalhes do pagamento via API Mercado Pago
        # e ativar a assinatura do usuário correspondente
        # Exemplo simplificado:
        # user_id, plano_id, periodicidade = ... (parse do external_reference)
        # Assinatura.objects.create(...)
    return HttpResponse(status=200)
