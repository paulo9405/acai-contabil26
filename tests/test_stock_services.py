"""
Testes dos services do app stock.
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from stock.models import StockCategory, StockCheck, StockCheckItem, StockItem
from stock.services import get_or_create_today_check, save_stock_check


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(db):
    return User.objects.create_user(username="func", password="pass")


@pytest.fixture
def category(db):
    return StockCategory.objects.create(name="Frutas", sort_order=1)


@pytest.fixture
def item(db, category):
    return StockItem.objects.create(category=category, name="Banana", sort_order=1)


@pytest.fixture
def item2(db, category):
    return StockItem.objects.create(category=category, name="Morango", sort_order=2)


@pytest.fixture
def today_check(db, user):
    return StockCheck.objects.create(date=timezone.localdate(), created_by=user)


# ---------------------------------------------------------------------------
# get_or_create_today_check
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetOrCreateTodayCheck:
    def test_creates_new_check(self, user):
        check = get_or_create_today_check(user=user)
        assert check.pk is not None
        assert check.date == timezone.localdate()
        assert check.created_by == user

    def test_returns_existing_check(self, user, today_check):
        check = get_or_create_today_check(user=user)
        assert check.pk == today_check.pk

    def test_existing_check_preserves_original_creator(self, user, today_check):
        other = User.objects.create_user(username="other", password="pass")
        check = get_or_create_today_check(user=other)
        # created_by permanece como o usuário original
        assert check.created_by == user


# ---------------------------------------------------------------------------
# save_stock_check
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSaveStockCheck:
    def test_creates_out_item(self, today_check, item):
        save_stock_check(stock_check=today_check, statuses={item.pk: "OUT"})
        sci = today_check.items.get(item=item)
        assert sci.status == "OUT"
        assert sci.item_name == item.name

    def test_creates_low_item(self, today_check, item):
        save_stock_check(stock_check=today_check, statuses={item.pk: "LOW"})
        sci = today_check.items.get(item=item)
        assert sci.status == "LOW"

    def test_empty_statuses_clears_all(self, today_check, item):
        StockCheckItem.objects.create(
            stock_check=today_check, item=item, item_name=item.name, status="OUT"
        )
        save_stock_check(stock_check=today_check, statuses={})
        assert today_check.items.count() == 0

    def test_removes_item_when_returned_to_ok(self, today_check, item, item2):
        StockCheckItem.objects.create(
            stock_check=today_check, item=item, item_name=item.name, status="OUT"
        )
        StockCheckItem.objects.create(
            stock_check=today_check, item=item2, item_name=item2.name, status="LOW"
        )
        # Banana voltou para OK; só Morango fica
        save_stock_check(stock_check=today_check, statuses={item2.pk: "LOW"})
        assert today_check.items.count() == 1
        assert today_check.items.first().item == item2

    def test_updates_status_of_existing_item(self, today_check, item):
        StockCheckItem.objects.create(
            stock_check=today_check, item=item, item_name=item.name, status="LOW"
        )
        save_stock_check(stock_check=today_check, statuses={item.pk: "OUT"})
        sci = today_check.items.get(item=item)
        assert sci.status == "OUT"

    def test_no_duplicate_items_created(self, today_check, item):
        save_stock_check(stock_check=today_check, statuses={item.pk: "LOW"})
        save_stock_check(stock_check=today_check, statuses={item.pk: "LOW"})
        assert today_check.items.count() == 1

    def test_snapshot_uses_current_item_name(self, today_check, item):
        save_stock_check(stock_check=today_check, statuses={item.pk: "OUT"})
        sci = today_check.items.get(item=item)
        assert sci.item_name == "Banana"

    def test_updates_check_timestamp(self, today_check, item):
        original_ts = today_check.updated_at
        save_stock_check(stock_check=today_check, statuses={item.pk: "OUT"})
        today_check.refresh_from_db()
        assert today_check.updated_at >= original_ts
