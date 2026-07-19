"""
Testes dos models do app stock.
"""

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from stock.models import StockCategory, StockCheck, StockCheckItem, StockItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(db):
    return User.objects.create_user(username="func_teste", password="pass")


@pytest.fixture
def category(db):
    return StockCategory.objects.create(name="Frutas", sort_order=1)


@pytest.fixture
def item(db, category):
    return StockItem.objects.create(category=category, name="Banana", sort_order=1)


@pytest.fixture
def stock_check(db, user):
    return StockCheck.objects.create(date=timezone.localdate(), created_by=user)


# ---------------------------------------------------------------------------
# StockCategory
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCategory:
    def test_str(self, category):
        assert str(category) == "Frutas"

    def test_active_default(self, db):
        cat = StockCategory.objects.create(name="Bases", sort_order=2)
        assert cat.active is True

    def test_name_unique(self, category):
        with pytest.raises(IntegrityError):
            StockCategory.objects.create(name="Frutas", sort_order=99)

    def test_ordering(self, db):
        StockCategory.objects.create(name="Zzz", sort_order=99)
        StockCategory.objects.create(name="Aaa", sort_order=1)
        first = StockCategory.objects.first()
        assert first.name == "Aaa"


# ---------------------------------------------------------------------------
# StockItem
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockItem:
    def test_str(self, item, category):
        assert str(item) == "Frutas / Banana"

    def test_active_default(self, db, category):
        it = StockItem.objects.create(category=category, name="Morango", sort_order=2)
        assert it.active is True

    def test_unique_per_category(self, item, category):
        with pytest.raises(IntegrityError):
            StockItem.objects.create(category=category, name="Banana", sort_order=99)

    def test_same_name_different_categories(self, db, item):
        cat2 = StockCategory.objects.create(name="Sorvetes", sort_order=2)
        # "Morango" já existe em Frutas; deve poder existir em Sorvetes
        it2 = StockItem.objects.create(category=cat2, name="Morango", sort_order=1)
        assert it2.pk is not None


# ---------------------------------------------------------------------------
# StockCheck
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCheck:
    def test_str(self, stock_check):
        date_str = timezone.localdate().strftime("%d/%m/%Y")
        assert str(stock_check) == f"Conferência {date_str}"

    def test_date_unique(self, stock_check, user):
        with pytest.raises(IntegrityError):
            StockCheck.objects.create(date=timezone.localdate(), created_by=user)

    def test_item_count_zero_when_empty(self, stock_check):
        assert stock_check.item_count == 0

    def test_item_count_reflects_marked_items(self, stock_check, item):
        StockCheckItem.objects.create(
            stock_check=stock_check,
            item=item,
            item_name=item.name,
            status=StockCheckItem.Status.OUT,
        )
        assert stock_check.item_count == 1


# ---------------------------------------------------------------------------
# StockCheckItem
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCheckItem:
    def test_str_out(self, stock_check, item):
        sci = StockCheckItem.objects.create(
            stock_check=stock_check,
            item=item,
            item_name="Banana",
            status=StockCheckItem.Status.OUT,
        )
        assert str(sci) == "Banana — Acabou"

    def test_str_low(self, stock_check, item):
        sci = StockCheckItem.objects.create(
            stock_check=stock_check,
            item=item,
            item_name="Banana",
            status=StockCheckItem.Status.LOW,
        )
        assert str(sci) == "Banana — Estoque baixo"

    def test_unique_item_per_check(self, stock_check, item):
        StockCheckItem.objects.create(
            stock_check=stock_check,
            item=item,
            item_name=item.name,
            status=StockCheckItem.Status.LOW,
        )
        with pytest.raises(IntegrityError):
            StockCheckItem.objects.create(
                stock_check=stock_check,
                item=item,
                item_name=item.name,
                status=StockCheckItem.Status.OUT,
            )

    def test_status_choices(self):
        assert StockCheckItem.Status.LOW == "LOW"
        assert StockCheckItem.Status.OUT == "OUT"
        labels = dict(StockCheckItem.Status.choices)
        assert labels["LOW"] == "Estoque baixo"
        assert labels["OUT"] == "Acabou"

    def test_snapshot_preserves_name(self, stock_check, item):
        sci = StockCheckItem.objects.create(
            stock_check=stock_check,
            item=item,
            item_name="Nome Original",
            status=StockCheckItem.Status.OUT,
        )
        item.name = "Nome Alterado"
        item.save()
        sci.refresh_from_db()
        assert sci.item_name == "Nome Original"
