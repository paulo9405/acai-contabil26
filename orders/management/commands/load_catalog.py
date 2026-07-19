"""
Management command para carregar o cardápio inicial da Açaí da Rose.

Idempotente: pode ser executado múltiplas vezes sem duplicar registros.
Execução MANUAL apenas — não roda no deploy automático (decisão P-09).

Uso:
    python manage.py load_catalog
    python manage.py load_catalog --dry-run  (apenas conta o que seria criado)
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Addon, Product, ProductCategory, ProductVariant, Size

# ---------------------------------------------------------------------------
# Dados do cardápio
# ---------------------------------------------------------------------------

SIZES = [
    {"name": "300 ml", "volume_ml": 300, "sort_order": 1},
    {"name": "500 ml", "volume_ml": 500, "sort_order": 2},
    {"name": "700 ml", "volume_ml": 700, "sort_order": 3},
    {"name": "1 litro", "volume_ml": 1000, "sort_order": 4},
    {"name": "1,5 litro", "volume_ml": 1500, "sort_order": 5},
    {"name": "2 litros", "volume_ml": 2000, "sort_order": 6},
]

CATEGORIES = [
    {"name": "Monte seu Açaí", "kind": ProductCategory.Kind.BUILD_YOUR_OWN, "sort_order": 1},
    {"name": "Açaís Prontos", "kind": ProductCategory.Kind.STANDARD, "sort_order": 2},
    {"name": "Sorvetes", "kind": ProductCategory.Kind.STANDARD, "sort_order": 3},
    {"name": "Vitaminas", "kind": ProductCategory.Kind.STANDARD, "sort_order": 4},
    {"name": "Adicionais", "kind": ProductCategory.Kind.ADDON, "sort_order": 5},
]

# Adicionais pagos (avulsos). is_free_option=True = elegível como grátis no Monte seu Açaí.
ADDONS = [
    # name                      price   is_free_option  sort_order
    ("Abacaxi", "4.00", False, 1),
    ("Amendoim granulado", "3.00", True, 2),
    ("Banana", "3.00", True, 3),
    ("Bis", "3.50", True, 4),
    ("Bis Oreo", "4.00", False, 5),
    ("Biscoito Oreo", "3.00", True, 6),
    ("Bombom", "5.00", False, 7),
    ("Calda de chocolate", "3.00", True, 8),
    ("Calda de morango", "3.00", True, 9),
    ("Canudo", "4.00", False, 10),
    ("Cereal mix", "3.50", True, 11),
    ("Confete", "4.00", False, 12),
    ("Cupuaçu", "6.00", False, 13),
    ("Gotas de chocolate", "4.50", False, 14),
    ("Granola", "3.00", True, 15),
    ("Kitkat", "5.00", False, 16),
    ("Kiwi", "7.00", False, 17),
    ("Laka", "7.50", False, 18),
    ("Leite condensado", "3.50", True, 19),
    ("Leite Ninho", "3.50", True, 20),
    ("Maltine", "4.00", False, 21),
    ("Morango", "6.50", False, 22),
    ("Nutella", "7.50", False, 23),
    ("Paçoca", "3.00", True, 24),
    ("Sorvete", "5.00", True, 25),
    ("Uva", "7.50", False, 26),
    ("Whey", "6.50", False, 27),
]

# Monte seu Açaí: included_addons_limit por tamanho
MONTE_ACAI_VARIANTS = [
    # (size_name, price, included_addons_limit)
    ("300 ml", "18.00", 2),
    ("500 ml", "24.00", 3),
    ("700 ml", "28.00", 3),
    ("1 litro", "38.00", 4),
    ("1,5 litro", "50.00", 5),
    ("2 litros", "64.00", 6),
]

# Açaís Prontos: (produto, sort_order, {size_name: price})
# None = tamanho não disponível para esse produto
ACAIS_PRONTOS = [
    (
        "01 Açaí Puro",
        1,
        {
            "300 ml": "16.00",
            "500 ml": "18.00",
            "700 ml": "24.00",
            "1 litro": "32.00",
            "1,5 litro": "50.00",
            "2 litros": "62.00",
        },
    ),
    (
        "02 Açaí Puro c/ Cupuaçu",
        2,
        {
            "300 ml": "18.00",
            "500 ml": "22.00",
            "700 ml": "26.00",
            "1 litro": "36.00",
            "1,5 litro": "52.00",
            "2 litros": "64.00",
        },
    ),
    (
        "03 Açaí Gotas de Chocolate",
        3,
        {
            "300 ml": "20.00",
            "500 ml": "25.00",
            "700 ml": "28.00",
            "1 litro": "38.00",
            "1,5 litro": "54.00",
            "2 litros": "64.00",
        },
    ),
    (
        "04 Açaí Ninho",
        4,
        {
            "300 ml": "18.00",
            "500 ml": "22.00",
            "700 ml": "26.00",
            "1 litro": "36.00",
            "1,5 litro": "52.00",
            "2 litros": "64.00",
        },
    ),
    (
        "05 Açaí Ninho c/ Cupuaçu",
        5,
        {
            "300 ml": "20.00",
            "500 ml": "26.00",
            "700 ml": "32.00",
            "1 litro": "40.00",
            "1,5 litro": "54.00",
            "2 litros": "56.00",
        },
    ),
    (
        "06 Açaí Maltine",
        6,
        {
            "300 ml": "18.00",
            "500 ml": "24.00",
            "700 ml": "28.00",
            "1 litro": "37.00",
            "1,5 litro": "53.00",
            "2 litros": "62.00",
        },
    ),
    (
        "07 Açaí Kids",
        7,
        {
            "300 ml": "19.00",
            "500 ml": "25.00",
            "700 ml": "29.00",
            "1 litro": "40.00",
            "1,5 litro": "54.00",
            "2 litros": "62.00",
        },
    ),
    (
        "08 Açaí Frutas",
        8,
        {
            "300 ml": "20.00",
            "500 ml": "27.00",
            "700 ml": "30.00",
            "1 litro": "39.00",
            "1,5 litro": "55.00",
            "2 litros": "63.00",
        },
    ),
    (
        "09 Açaí Nutella",
        9,
        {
            "300 ml": "22.00",
            "500 ml": "30.00",
            "700 ml": "36.00",
            "1 litro": "50.00",
            "1,5 litro": "59.00",
            "2 litros": "68.00",
        },
    ),
    (
        "10 Combo Família",
        10,
        {
            "1,5 litro": "60.00",
            "2 litros": "72.00",
        },
    ),
    (
        "11 Açaí Zero",
        11,
        {
            "300 ml": "18.00",
            "500 ml": "24.00",
            "700 ml": "28.00",
            "1 litro": "39.50",
        },
    ),
    (
        "12 Açaí Gourmet",
        12,
        {
            "300 ml": "21.00",
            "500 ml": "29.00",
            "700 ml": "34.00",
            "1 litro": "49.00",
            "1,5 litro": "54.00",
            "2 litros": "65.00",
        },
    ),
    (
        "13 Açaí Oreo",
        13,
        {
            "300 ml": "19.00",
            "500 ml": "26.00",
            "700 ml": "30.00",
            "1 litro": "48.00",
            "1,5 litro": "53.00",
            "2 litros": "62.00",
        },
    ),
    (
        "14 Cupuaçu",
        14,
        {
            "300 ml": "16.50",
            "500 ml": "18.50",
            "700 ml": "24.50",
            "1 litro": "35.00",
            "1,5 litro": "52.00",
            "2 litros": "64.00",
        },
    ),
    (
        "15 Raspa de Chocolate com Cupuaçu",
        15,
        {
            "300 ml": "15.00",
            "500 ml": "20.00",
            "700 ml": "22.00",
            "1 litro": "32.00",
        },
    ),
    (
        "16 Açaí Paçoquinha",
        16,
        {
            "1 litro": "48.00",
            "1,5 litro": "58.00",
            "2 litros": "66.00",
        },
    ),
]

# Sorvetes: pote 2 litros (sem tamanho — size=None)
SORVETES = [
    ("Sorvete Morango", "36.00", 1),
    ("Sorvete Flocos", "36.00", 2),
    ("Sorvete Laka", "33.00", 3),
    ("Sorvete Coco/Abacaxi", "36.00", 4),
    ("Sorvete Chocolate", "36.00", 5),
    ("Sorvete Ninho Trufado", "39.00", 6),
    ("Sorvete Napolitano", "37.00", 7),
]

# Vitaminas: 500 ml fixo
VITAMINAS = [
    ("Vitamina Whey Protein", "25.00", "Açaí zero, whey, leite e banana", 1),
    ("Vitamina Açaí c/ Nutella", "24.00", "Açaí, leite, banana e nutella", 2),
    ("Vitamina Açaí Tradicional", "20.00", "Açaí, leite e banana", 3),
]


class Command(BaseCommand):
    help = "Carrega o cardápio inicial da Açaí da Rose (idempotente)"

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
            self._load_sizes(dry_run, counters)
            self._load_categories(dry_run, counters)
            self._load_addons(dry_run, counters)
            self._load_monte_acai(dry_run, counters)
            self._load_acais_prontos(dry_run, counters)
            self._load_sorvetes(dry_run, counters)
            self._load_vitaminas(dry_run, counters)

            if dry_run:
                # Desfaz tudo em dry-run
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
    # Helpers internos
    # -----------------------------------------------------------------------

    def _upsert(self, model, lookup, defaults, dry_run, counters, label=""):
        if dry_run:
            exists = model.objects.filter(**lookup).exists()
            if exists:
                counters["unchanged"] += 1
            else:
                counters["created"] += 1
                self.stdout.write(f"  [criar] {label or str(lookup)}")
            return None, not exists

        obj, created = model.objects.get_or_create(**lookup, defaults=defaults)

        if not created:
            changed = False
            for field, value in defaults.items():
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.save()
                counters["updated"] += 1
            else:
                counters["unchanged"] += 1
        else:
            counters["created"] += 1

        return obj, created

    def _get_size(self, name):
        return Size.objects.get(name=name)

    def _get_category(self, name):
        return ProductCategory.objects.get(name=name)

    # -----------------------------------------------------------------------
    # Loaders
    # -----------------------------------------------------------------------

    def _load_sizes(self, dry_run, counters):
        self.stdout.write("Tamanhos...")
        for data in SIZES:
            self._upsert(
                Size,
                lookup={"name": data["name"]},
                defaults={
                    "volume_ml": data["volume_ml"],
                    "sort_order": data["sort_order"],
                    "active": True,
                },
                dry_run=dry_run,
                counters=counters,
                label=data["name"],
            )

    def _load_categories(self, dry_run, counters):
        self.stdout.write("Categorias...")
        for data in CATEGORIES:
            self._upsert(
                ProductCategory,
                lookup={"name": data["name"]},
                defaults={"kind": data["kind"], "sort_order": data["sort_order"], "active": True},
                dry_run=dry_run,
                counters=counters,
                label=data["name"],
            )

    def _load_addons(self, dry_run, counters):
        self.stdout.write("Adicionais...")
        for name, price, is_free, sort_order in ADDONS:
            self._upsert(
                Addon,
                lookup={"name": name},
                defaults={
                    "price": Decimal(price),
                    "is_free_option": is_free,
                    "sort_order": sort_order,
                    "active": True,
                },
                dry_run=dry_run,
                counters=counters,
                label=name,
            )

    def _load_monte_acai(self, dry_run, counters):
        self.stdout.write("Monte seu Açaí...")
        if not dry_run:
            cat = self._get_category("Monte seu Açaí")
        else:
            cat = None

        product, _ = self._upsert(
            Product,
            lookup={"name": "Monte seu Açaí"},
            defaults={
                "category": cat,
                "description": "",
                "product_type": Product.ProductType.BUILD_YOUR_OWN,
                "sort_order": 1,
                "active": True,
            },
            dry_run=dry_run,
            counters=counters,
            label="Monte seu Açaí (produto)",
        )

        if dry_run:
            for size_name, price, limit in MONTE_ACAI_VARIANTS:
                self.stdout.write(f"  [criar?] Monte seu Açaí — {size_name}")
            return

        for size_name, price, limit in MONTE_ACAI_VARIANTS:
            size = self._get_size(size_name)
            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                size=size,
                defaults={
                    "price": Decimal(price),
                    "included_addons_limit": limit,
                    "active": True,
                },
            )
            if not created:
                changed = variant.price != Decimal(price) or variant.included_addons_limit != limit
                if changed:
                    variant.price = Decimal(price)
                    variant.included_addons_limit = limit
                    variant.save()
                    counters["updated"] += 1
                else:
                    counters["unchanged"] += 1
            else:
                counters["created"] += 1

    def _load_acais_prontos(self, dry_run, counters):
        self.stdout.write("Açaís Prontos...")
        if not dry_run:
            cat = self._get_category("Açaís Prontos")
        else:
            cat = None

        for name, sort_order, variants in ACAIS_PRONTOS:
            product, _ = self._upsert(
                Product,
                lookup={"name": name},
                defaults={
                    "category": cat,
                    "description": "",
                    "product_type": Product.ProductType.STANDARD,
                    "sort_order": sort_order,
                    "active": True,
                },
                dry_run=dry_run,
                counters=counters,
                label=name,
            )

            if dry_run:
                continue

            for size_name, price in variants.items():
                size = self._get_size(size_name)
                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    size=size,
                    defaults={"price": Decimal(price), "active": True},
                )
                if not created:
                    if variant.price != Decimal(price):
                        variant.price = Decimal(price)
                        variant.save()
                        counters["updated"] += 1
                    else:
                        counters["unchanged"] += 1
                else:
                    counters["created"] += 1

    def _load_sorvetes(self, dry_run, counters):
        self.stdout.write("Sorvetes...")
        if not dry_run:
            cat = self._get_category("Sorvetes")
        else:
            cat = None

        for name, price, sort_order in SORVETES:
            product, _ = self._upsert(
                Product,
                lookup={"name": name},
                defaults={
                    "category": cat,
                    "description": "Pote 2 litros",
                    "product_type": Product.ProductType.STANDARD,
                    "sort_order": sort_order,
                    "active": True,
                },
                dry_run=dry_run,
                counters=counters,
                label=name,
            )

            if dry_run:
                continue

            # Sorvetes não têm tamanho (pote fixo 2 litros)
            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                size=None,
                defaults={"price": Decimal(price), "active": True},
            )
            if not created:
                if variant.price != Decimal(price):
                    variant.price = Decimal(price)
                    variant.save()
                    counters["updated"] += 1
                else:
                    counters["unchanged"] += 1
            else:
                counters["created"] += 1

    def _load_vitaminas(self, dry_run, counters):
        self.stdout.write("Vitaminas...")
        if not dry_run:
            cat = self._get_category("Vitaminas")
            size_500 = self._get_size("500 ml")
        else:
            cat = None
            size_500 = None

        for name, price, description, sort_order in VITAMINAS:
            product, _ = self._upsert(
                Product,
                lookup={"name": name},
                defaults={
                    "category": cat,
                    "description": description,
                    "product_type": Product.ProductType.STANDARD,
                    "sort_order": sort_order,
                    "active": True,
                },
                dry_run=dry_run,
                counters=counters,
                label=name,
            )

            if dry_run:
                continue

            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                size=size_500,
                defaults={"price": Decimal(price), "active": True},
            )
            if not created:
                if variant.price != Decimal(price):
                    variant.price = Decimal(price)
                    variant.save()
                    counters["updated"] += 1
                else:
                    counters["unchanged"] += 1
            else:
                counters["created"] += 1
