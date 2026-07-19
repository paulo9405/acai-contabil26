"""
Context processors da aplicação finance.

Disponibiliza variáveis globais para todos os templates,
evitando repetição de strings em múltiplos arquivos.
"""

NAV_LABELS = {
    "NAV_INICIO": "Início",
    "NAV_FECHAMENTO": "Fechamento do Dia",
    "NAV_HISTORICO": "Histórico",
    "NAV_RELATORIOS": "Relatórios",
    "NAV_PEDIDOS": "Pedidos",
    "NAV_ESTOQUE": "Conferência de Estoque",
}


def nav_labels(request):
    """Injeta os labels do menu principal em todos os templates."""
    return NAV_LABELS
