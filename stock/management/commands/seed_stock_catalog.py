"""
Management command para carregar o catálogo inicial de itens de estoque.

Idempotente: pode ser executado múltiplas vezes sem duplicar registros.
Execução MANUAL apenas — não roda no deploy automático.

Uso:
    python manage.py seed_stock_catalog
    python manage.py seed_stock_catalog --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from stock.models import StockCategory, StockItem

# ---------------------------------------------------------------------------
# Catálogo de itens de estoque
# ---------------------------------------------------------------------------

CATALOG = [
    {
        "name": "Bases",
        "sort_order": 1,
        "items": [
            {"name": "Açaí", "sort_order": 1},
            {"name": "Açaí Zero", "sort_order": 2},
            {"name": "Cupuaçu", "sort_order": 3},
        ],
    },
    {
        "name": "Frutas",
        "sort_order": 2,
        "items": [
            {"name": "Abacaxi", "sort_order": 1},
            {"name": "Banana", "sort_order": 2},
            {"name": "Kiwi", "sort_order": 3},
            {"name": "Morango", "sort_order": 4},
            {"name": "Uva", "sort_order": 5},
        ],
    },
    {
        "name": "Coberturas e Cremes",
        "sort_order": 3,
        "items": [
            {"name": "Calda de Chocolate", "sort_order": 1},
            {"name": "Calda de Morango", "sort_order": 2},
            {"name": "Leite Condensado", "sort_order": 3},
            {"name": "Leite Ninho", "sort_order": 4},
            {"name": "Nutella", "sort_order": 5},
        ],
    },
    {
        "name": "Adicionais",
        "sort_order": 4,
        "items": [
            {"name": "Amendoim", "sort_order": 1},
            {"name": "Bis", "sort_order": 2},
            {"name": "Bis Oreo", "sort_order": 3},
            {"name": "Bombom", "sort_order": 4},
            {"name": "Canudo", "sort_order": 5},
            {"name": "Cereal Mix", "sort_order": 6},
            {"name": "Confete", "sort_order": 7},
            {"name": "Gotas de Chocolate", "sort_order": 8},
            {"name": "Granola", "sort_order": 9},
            {"name": "KitKat", "sort_order": 10},
            {"name": "Laka", "sort_order": 11},
            {"name": "Maltine", "sort_order": 12},
            {"name": "Oreo", "sort_order": 13},
            {"name": "Paçoca", "sort_order": 14},
            {"name": "Sorvete (adicional)", "sort_order": 15},
            {"name": "Whey Protein", "sort_order": 16},
        ],
    },
    {
        "name": "Sorvetes",
        "sort_order": 5,
        "items": [
            {"name": "Chocolate", "sort_order": 1},
            {"name": "Coco/Abacaxi", "sort_order": 2},
            {"name": "Flocos", "sort_order": 3},
            {"name": "Laka", "sort_order": 4},
            {"name": "Morango", "sort_order": 5},
            {"name": "Napolitano", "sort_order": 6},
            {"name": "Ninho Trufado", "sort_order": 7},
        ],
    },
    {
        "name": "Embalagens",
        "sort_order": 6,
        "items": [
            {"name": "Canudinho", "sort_order": 1},
            {"name": "Colher de plástico", "sort_order": 2},
            {"name": "Copo 300 ml", "sort_order": 3},
            {"name": "Copo 500 ml", "sort_order": 4},
            {"name": "Copo 700 ml", "sort_order": 5},
            {"name": "Copo de caldão", "sort_order": 6},
            {"name": "Garrafa de vitamina", "sort_order": 7},
            {"name": "Pote 1 litro", "sort_order": 8},
            {"name": "Pote 1,5 litro", "sort_order": 9},
            {"name": "Pote 2 litros", "sort_order": 10},
            {"name": "Sacolinha fina", "sort_order": 11},
            {"name": "Sacolinha grossa", "sort_order": 12},
        ],
    },
    {
        "name": "Materiais de apoio",
        "sort_order": 7,
        "items": [
            {"name": "Bloco de pedidos", "sort_order": 1},
            {"name": "Bobina da máquina de cartão", "sort_order": 2},
            {"name": "Caneta", "sort_order": 3},
            {"name": "Grampo de grampeador", "sort_order": 4},
        ],
    },
]


class Command(BaseCommand):
    help = "Carrega o catálogo inicial de itens para conferência de estoque (idempotente)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas exibe o que seria criado, sem salvar",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("Modo dry-run: nenhum dado será salvo.\n"))

        counters = {"created": 0, "updated": 0, "unchanged": 0}

        with transaction.atomic():
            for cat_data in CATALOG:
                self._upsert_category(cat_data, dry_run, counters)

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído — criados: {counters['created']}, "
                f"atualizados: {counters['updated']}, "
                f"sem alteração: {counters['unchanged']}"
            )
        )

    # -----------------------------------------------------------------------

    def _upsert_category(self, cat_data, dry_run, counters):
        name = cat_data["name"]
        self.stdout.write(f"{name}...")

        if dry_run:
            exists = StockCategory.objects.filter(name=name).exists()
            if exists:
                counters["unchanged"] += 1
            else:
                counters["created"] += 1
                self.stdout.write(f"  [criar] {name}")
            for item_data in cat_data["items"]:
                self._upsert_item_dry(name, item_data, counters)
            return

        category, cat_created = StockCategory.objects.get_or_create(
            name=name,
            defaults={"sort_order": cat_data["sort_order"], "active": True},
        )
        if cat_created:
            counters["created"] += 1
        else:
            changed = category.sort_order != cat_data["sort_order"]
            if changed:
                category.sort_order = cat_data["sort_order"]
                category.save(update_fields=["sort_order"])
                counters["updated"] += 1
            else:
                counters["unchanged"] += 1

        for item_data in cat_data["items"]:
            self._upsert_item(category, item_data, counters)

    def _upsert_item_dry(self, cat_name, item_data, counters):
        exists = StockItem.objects.filter(
            category__name=cat_name, name=item_data["name"]
        ).exists()
        if exists:
            counters["unchanged"] += 1
        else:
            counters["created"] += 1
            self.stdout.write(f"  [criar] {item_data['name']}")

    def _upsert_item(self, category, item_data, counters):
        item, created = StockItem.objects.get_or_create(
            category=category,
            name=item_data["name"],
            defaults={"sort_order": item_data["sort_order"], "active": True},
        )
        if created:
            counters["created"] += 1
        else:
            changed = item.sort_order != item_data["sort_order"]
            if changed:
                item.sort_order = item_data["sort_order"]
                item.save(update_fields=["sort_order"])
                counters["updated"] += 1
            else:
                counters["unchanged"] += 1
