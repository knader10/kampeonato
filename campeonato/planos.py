"""
Módulo para gerenciamento de planos e assinaturas
"""
import json
from typing import Dict, List, Optional

class PlanoManager:
    """Classe para gerenciar planos e preços"""
    
    def __init__(self):
        self.planos_data = {
            "descontos": {
                "trimestral": {
                    "descricao": "Pagamento trimestral (10% de desconto)",
                    "percentual": 10
                },
                "anual": {
                    "descricao": "Pagamento anual (15% de desconto)",
                    "percentual": 15
                }
            },
            "planos": [
                {
                    "id": "basico",
                    "nome": "Básico",
                    "precos": {
                        "mensal": 14.97,
                        "trimestral": 40.42,
                        "anual": 152.36
                    },
                    "recursos": [
                        "Até 70 jogadores por campeonato",
                        "Até 1 patrocinador",
                        "Até 3 campeonatos",
                        "Site personalizado para redes",
                        "Exportação de dados em Excel",
                    ],
                    "links": {
                        "mensal": "https://checkout.stripe.com/basico-mensal",
                        "trimestral": "https://checkout.stripe.com/basico-trimestral",
                        "anual": "https://checkout.stripe.com/basico-anual"
                    }
                },
                {
                    "id": "pro",
                    "nome": "Pró",
                    "precos": {
                        "mensal": 33.97,
                        "trimestral": 91.72,
                        "anual": 346.42
                    },
                    "recursos": [
                        "Até 230 jogadores por campeonato",
                        "Sem limite de patrocinadores",
                        "Sem limite de campeonatos",
                        "Site personalizado para redes",
                        "Exportação de dados em Excel"
                    ],
                    "links": {
                        "mensal": "https://checkout.stripe.com/pro-mensal",
                        "trimestral": "https://checkout.stripe.com/pro-trimestral",
                        "anual": "https://checkout.stripe.com/pro-anual"
                    }
                },
                {
                    "id": "premium",
                    "nome": "Premium",
                    "precos": {
                        "mensal": 49.97,
                        "trimestral": 134.91,
                        "anual": 509.70
                    },
                    "recursos": [
                        "Até 500 jogadores por campeonato",
                        "Sem limite de patrocinadores",
                        "Sem limite de campeonatos",
                        "Site personalizado",
                        "Exportação de dados em Excel"
                    ],
                    "links": {
                        "mensal": "https://checkout.stripe.com/premium-mensal",
                        "trimestral": "https://checkout.stripe.com/premium-trimestral",
                        "anual": "https://checkout.stripe.com/premium-anual"
                    }
                },
                {
                    "id": "personalizado",
                    "nome": "Personalizado",
                    "precos": {
                        "mensal": None,
                        "trimestral": None,
                        "anual": None
                    },
                    "recursos": [
                        "Plano exclusivo para suas necessidades específicas"
                    ],
                    "botao": "Contatar via WhatsApp",
                    "whatsapp_link": "https://wa.me/5571982105992?text=Olá! Gostaria de saber mais sobre o Plano Personalizado do Kampeonato."
                }
            ]
        }
    
    def get_planos_data(self) -> Dict:
        """Retorna todos os dados dos planos"""
        return self.planos_data
    
    def get_plano_by_id(self, plano_id: str) -> Optional[Dict]:
        """Retorna um plano específico pelo ID"""
        for plano in self.planos_data["planos"]:
            if plano["id"] == plano_id:
                return plano
        return None
    
    def get_preco_plano(self, plano_id: str, periodicidade: str) -> Optional[float]:
        """Retorna o preço de um plano específico por periodicidade"""
        plano = self.get_plano_by_id(plano_id)
        if plano and periodicidade in plano["precos"]:
            return plano["precos"][periodicidade]
        return None
    
    def get_link_pagamento(self, plano_id: str, periodicidade: str) -> Optional[str]:
        """Retorna o link de pagamento para um plano e periodicidade específicos"""
        plano = self.get_plano_by_id(plano_id)
        if plano and "links" in plano and periodicidade in plano["links"]:
            return plano["links"][periodicidade]
        return None
    
    def get_desconto_info(self, periodicidade: str) -> Optional[Dict]:
        """Retorna informações de desconto para uma periodicidade"""
        if periodicidade in self.planos_data["descontos"]:
            return self.planos_data["descontos"][periodicidade]
        return None



# Helper robusto para verificar se o usuário tem plano ativo
def usuario_tem_plano_ativo(user) -> bool:
    """
    Verifica se o usuário possui um plano ativo de verdade.
    Considera assinatura ativa se existir uma assinatura com status 'ativo' e data de validade maior ou igual a hoje.
    Superusers sempre têm acesso total.
    """
    # Superusers sempre têm acesso
    if user.is_superuser:
        return True
        
    from datetime import date
    try:
        # Ajuste o import/modelo conforme seu projeto
        from adminpanel.models import Assinatura
        hoje = date.today()
        return Assinatura.objects.filter(user=user, status='ativo', validade__gte=hoje).exists()
    except Exception:
        return False


def get_usuario_plano_atual(user) -> Optional[str]:
    """
    Retorna o ID do plano atual do usuário, se houver.
    Superusers têm plano 'admin'.
    """
    # Superusers têm plano especial
    if user.is_superuser:
        return "admin"
        
    if usuario_tem_plano_ativo(user):
        # Exemplo: retornar o plano do usuário
        # return user.assinatura_set.get(status='ativo').plano_id
        return "pro"  # Simulação, ajuste conforme sua lógica
    return None


def get_usuario_assinatura_info(user) -> Optional[Dict]:
    """
    Retorna informações da assinatura atual do usuário, se houver.
    Para superusers, retorna informações especiais.
    """
    # Para superusers, retornar acesso total
    if user.is_superuser:
        return {
            "plano_id": "admin",
            "plano_nome": "Administrador",
            "status": "ativo",
            "data_renovacao": "Ilimitado",
            "periodicidade": "permanente",
            "preco_atual": 0.00,
            "dias_para_renovacao": "∞"
        }
    
    if not usuario_tem_plano_ativo(user):
        return None
    # Exemplo: buscar dados reais da assinatura
    return {
        "plano_id": get_usuario_plano_atual(user),
        "status": "ativo",
        "data_renovacao": "2025-08-05",
        "periodicidade": "mensal",
        "preco_atual": 33.97
    }
