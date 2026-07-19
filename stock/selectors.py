"""
Selectors for the stock app — read-only queries.
"""

from django.db.models import Prefetch

from stock.models import StockCategory, StockCheck, StockItem


def get_last_check():
    """Retorna a conferência mais recente ou None."""
    return StockCheck.objects.select_related("created_by").order_by("-date").first()


def get_active_catalog_with_status(*, stock_check):
    """
    Retorna o catálogo ativo agrupado por categoria, com o status atual de
    cada item na conferência informada.

    Itens sem registro em `stock_check` recebem status 'OK'.
    Retorna lista de dicts: [{'category': StockCategory, 'items': [StockItem, ...]}, ...]
    """
    status_map = {sci.item_id: sci.status for sci in stock_check.items.all()}

    categories = (
        StockCategory.objects.filter(active=True)
        .prefetch_related(
            Prefetch(
                "items",
                queryset=StockItem.objects.filter(active=True).order_by("sort_order", "name"),
            )
        )
        .order_by("sort_order", "name")
    )

    result = []
    for cat in categories:
        items = list(cat.items.all())
        if items:
            for item in items:
                item.current_status = status_map.get(item.pk, "OK")
            result.append({"category": cat, "items": items})
    return result


def get_check_detail(*, pk):
    """
    Retorna uma conferência pelo pk com itens pré-carregados.
    Levanta StockCheck.DoesNotExist se não encontrado.
    """
    return (
        StockCheck.objects.select_related("created_by")
        .prefetch_related("items")
        .get(pk=pk)
    )
