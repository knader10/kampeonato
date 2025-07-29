import mercadopago
from django.conf import settings

sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

def criar_preferencia_pagamento(user, plano_id, periodicidade, preco, success_url, failure_url, notification_url):
    # URLs públicas para Mercado Pago acessar (ngrok)
    NGROK_DOMAIN = "https://b0b3c0e45055.ngrok-free.app"  # Pode ser alterado conforme seu domínio ngrok ativo
    success_url_public = f"{NGROK_DOMAIN}/assinatura/sucesso/"
    failure_url_public = f"{NGROK_DOMAIN}/assinatura/erro/"
    notification_url_public = f"{NGROK_DOMAIN}/mercadopago/webhook/"
    preference_data = {
        "items": [
            {
                "title": f"Assinatura Kampeonato - Plano {plano_id.capitalize()} ({periodicidade})",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(preco),
            }
        ],
        "payer": {
            "email": user.email,
        },
        "back_urls": {
            "success": success_url_public,
            "failure": failure_url_public,
            "pending": failure_url_public,
        },
        "auto_return": "approved",
        "notification_url": notification_url_public,
        "external_reference": f"{user.id}:{plano_id}:{periodicidade}",
    }
    preference_response = sdk.preference().create(preference_data)
    return preference_response
