"""
Services for the stock app — business logic and writes.

Convenções:
- Funções keyword-only (*)
- Escrita e regras de negócio aqui; leitura em selectors.py
"""

from django.db import transaction
from django.utils import timezone

from stock.models import StockCheck, StockCheckItem, StockItem


def get_or_create_today_check(*, user):
    """
    Retorna a conferência de hoje, criando-a se ainda não existir.
    O `created_by` só é definido na criação; edições posteriores preservam o responsável original.
    """
    today = timezone.localdate()
    stock_check, _ = StockCheck.objects.get_or_create(
        date=today,
        defaults={"created_by": user},
    )
    return stock_check


def save_stock_check(*, stock_check, statuses):
    """
    Reconcilia os StockCheckItem de uma conferência.

    `statuses`: dict {item_id (int): 'LOW'|'OUT'}.
    Itens ausentes do dict são tratados como OK — suas linhas são removidas.
    """
    with transaction.atomic():
        existing = {sci.item_id: sci for sci in stock_check.items.all()}

        marked_ids = set(statuses.keys())
        existing_ids = set(existing.keys())

        to_delete = existing_ids - marked_ids
        if to_delete:
            StockCheckItem.objects.filter(stock_check=stock_check, item_id__in=to_delete).delete()

        for item_id, status in statuses.items():
            if item_id in existing:
                sci = existing[item_id]
                if sci.status != status:
                    sci.status = status
                    sci.save(update_fields=["status"])
            else:
                item = StockItem.objects.get(pk=item_id)
                StockCheckItem.objects.create(
                    stock_check=stock_check,
                    item=item,
                    item_name=item.name,
                    status=status,
                )

        stock_check.save(update_fields=["updated_at"])

    return stock_check


def build_shopping_list(*, stock_check):
    """
    Retorna {"out": [...], "low": [...]} com nomes em ordem alfabética.
    Grupos vazios são incluídos como listas vazias.
    """
    items = stock_check.items.order_by("item_name").values_list("status", "item_name")
    out_items = [name for status, name in items if status == StockCheckItem.Status.OUT]
    low_items = [name for status, name in items if status == StockCheckItem.Status.LOW]
    return {"out": out_items, "low": low_items}


def build_copy_text(*, shopping_list):
    """
    Formata a lista de compras para colar no WhatsApp.
    Retorna string vazia se a lista estiver vazia.
    """
    parts = []
    if shopping_list["out"]:
        lines = ["🔴 Acabou"]
        lines.extend(f"• {name}" for name in shopping_list["out"])
        parts.append("\n".join(lines))
    if shopping_list["low"]:
        lines = ["🟡 Estoque baixo"]
        lines.extend(f"• {name}" for name in shopping_list["low"])
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
