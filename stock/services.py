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


def save_stock_check(*, stock_check, statuses, quantities=None):
    """
    Reconcilia os StockCheckItem de uma conferência.

    `statuses`: dict {item_id (int): 'LOW'|'OUT'}.
    `quantities`: dict {item_id (int): str} — quantidade a comprar (opcional).
    Itens ausentes do dict são tratados como OK — suas linhas são removidas.
    """
    if quantities is None:
        quantities = {}

    with transaction.atomic():
        existing = {sci.item_id: sci for sci in stock_check.items.all()}

        marked_ids = set(statuses.keys())
        existing_ids = set(existing.keys())

        to_delete = existing_ids - marked_ids
        if to_delete:
            StockCheckItem.objects.filter(stock_check=stock_check, item_id__in=to_delete).delete()

        for item_id, status in statuses.items():
            qty = quantities.get(item_id, "")
            if item_id in existing:
                sci = existing[item_id]
                changed = []
                if sci.status != status:
                    sci.status = status
                    changed.append("status")
                if sci.buy_quantity != qty:
                    sci.buy_quantity = qty
                    changed.append("buy_quantity")
                if changed:
                    sci.save(update_fields=changed)
            else:
                item = StockItem.objects.get(pk=item_id)
                StockCheckItem.objects.create(
                    stock_check=stock_check,
                    item=item,
                    item_name=item.name,
                    status=status,
                    buy_quantity=qty,
                )

        stock_check.save(update_fields=["updated_at"])

    return stock_check


def build_shopping_list(*, stock_check):
    """
    Retorna {"out": [...], "low": [...]} com dicts {"name": str, "qty": str}.
    Ordem alfabética. Grupos vazios são incluídos como listas vazias.
    """
    rows = stock_check.items.order_by("item_name").values_list("status", "item_name", "buy_quantity")
    out_items = [{"name": n, "qty": q} for s, n, q in rows if s == StockCheckItem.Status.OUT]
    low_items = [{"name": n, "qty": q} for s, n, q in rows if s == StockCheckItem.Status.LOW]
    return {"out": out_items, "low": low_items}


def build_copy_text(*, shopping_list):
    """
    Formata a lista de compras para colar no WhatsApp.
    Inclui quantidade se preenchida. Retorna string vazia se a lista estiver vazia.
    """
    def fmt(item):
        return f"• {item['name']} — {item['qty']}" if item["qty"] else f"• {item['name']}"

    parts = []
    if shopping_list["out"]:
        lines = ["🔴 Acabou"]
        lines.extend(fmt(i) for i in shopping_list["out"])
        parts.append("\n".join(lines))
    if shopping_list["low"]:
        lines = ["🟡 Estoque baixo"]
        lines.extend(fmt(i) for i in shopping_list["low"])
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
