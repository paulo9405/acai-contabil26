"""
Testes da Fase 3: build_shopping_list, build_copy_text e StockCheckDetailView.
"""

import pytest
from django.contrib.auth.models import Group, User
from django.utils import timezone

from stock.models import StockCategory, StockCheck, StockCheckItem, StockItem
from stock.services import build_copy_text, build_shopping_list

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def operacao_user(db):
    user = User.objects.create_user(username="op3", password="pass")
    group, _ = Group.objects.get_or_create(name="Operacao")
    user.groups.add(group)
    return user


@pytest.fixture
def operacao_client(operacao_user):
    from django.test import Client

    c = Client()
    c.force_login(operacao_user)
    return c


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="regular3", password="pass")


@pytest.fixture
def category(db):
    return StockCategory.objects.create(name="Frutas", sort_order=1)


@pytest.fixture
def item_a(db, category):
    return StockItem.objects.create(category=category, name="Açaí", sort_order=1)


@pytest.fixture
def item_b(db, category):
    return StockItem.objects.create(category=category, name="Banana", sort_order=2)


@pytest.fixture
def item_c(db, category):
    return StockItem.objects.create(category=category, name="Cupuaçu", sort_order=3)


@pytest.fixture
def empty_check(db, operacao_user):
    return StockCheck.objects.create(date=timezone.localdate(), created_by=operacao_user)


@pytest.fixture
def check_with_items(db, operacao_user, item_a, item_b, item_c):
    check = StockCheck.objects.create(date=timezone.localdate(), created_by=operacao_user)
    StockCheckItem.objects.create(
        stock_check=check, item=item_a, item_name=item_a.name, status="OUT"
    )
    StockCheckItem.objects.create(
        stock_check=check, item=item_b, item_name=item_b.name, status="LOW"
    )
    StockCheckItem.objects.create(
        stock_check=check, item=item_c, item_name=item_c.name, status="OUT"
    )
    return check


# ---------------------------------------------------------------------------
# build_shopping_list
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBuildShoppingList:
    def test_empty_check_returns_empty_lists(self, empty_check):
        result = build_shopping_list(stock_check=empty_check)
        assert result == {"out": [], "low": []}

    def test_out_items_grouped_correctly(self, check_with_items):
        result = build_shopping_list(stock_check=check_with_items)
        assert "Açaí" in result["out"]
        assert "Cupuaçu" in result["out"]
        assert "Banana" not in result["out"]

    def test_low_items_grouped_correctly(self, check_with_items):
        result = build_shopping_list(stock_check=check_with_items)
        assert "Banana" in result["low"]
        assert "Açaí" not in result["low"]

    def test_out_items_sorted_alphabetically(self, check_with_items):
        result = build_shopping_list(stock_check=check_with_items)
        assert result["out"] == sorted(result["out"])

    def test_low_items_sorted_alphabetically(self, db, operacao_user, category):
        item_z = StockItem.objects.create(category=category, name="Zebu", sort_order=9)
        item_a = StockItem.objects.create(category=category, name="Abacate", sort_order=10)
        check = StockCheck.objects.create(date=timezone.localdate(), created_by=operacao_user)
        StockCheckItem.objects.create(
            stock_check=check, item=item_z, item_name=item_z.name, status="LOW"
        )
        StockCheckItem.objects.create(
            stock_check=check, item=item_a, item_name=item_a.name, status="LOW"
        )
        result = build_shopping_list(stock_check=check)
        assert result["low"] == ["Abacate", "Zebu"]


# ---------------------------------------------------------------------------
# build_copy_text
# ---------------------------------------------------------------------------


class TestBuildCopyText:
    def test_empty_list_returns_empty_string(self):
        result = build_copy_text(shopping_list={"out": [], "low": []})
        assert result == ""

    def test_only_out_items(self):
        result = build_copy_text(shopping_list={"out": ["Açaí", "Cupuaçu"], "low": []})
        assert "🔴 Acabou" in result
        assert "• Açaí" in result
        assert "• Cupuaçu" in result
        assert "🟡" not in result

    def test_only_low_items(self):
        result = build_copy_text(shopping_list={"out": [], "low": ["Banana"]})
        assert "🟡 Estoque baixo" in result
        assert "• Banana" in result
        assert "🔴" not in result

    def test_both_sections_separated_by_blank_line(self):
        result = build_copy_text(shopping_list={"out": ["Açaí"], "low": ["Banana"]})
        assert "🔴 Acabou" in result
        assert "🟡 Estoque baixo" in result
        assert "\n\n" in result

    def test_out_section_appears_before_low_section(self):
        result = build_copy_text(shopping_list={"out": ["Açaí"], "low": ["Banana"]})
        assert result.index("🔴") < result.index("🟡")


# ---------------------------------------------------------------------------
# StockCheckDetailView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCheckDetailView:
    def _url(self, pk):
        return f"/estoque/{pk}/"

    def test_requires_login(self, db, empty_check):
        from django.test import Client

        resp = Client().get(self._url(empty_check.pk))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]

    def test_denies_user_without_permission(self, regular_user, empty_check):
        from django.test import Client

        c = Client()
        c.force_login(regular_user)
        resp = c.get(self._url(empty_check.pk))
        assert resp.status_code == 403

    def test_accessible_for_operacao(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert resp.status_code == 200

    def test_returns_404_for_nonexistent_check(self, operacao_client):
        resp = operacao_client.get(self._url(9999))
        assert resp.status_code == 404

    def test_context_has_stock_check(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert resp.context["stock_check"].pk == empty_check.pk

    def test_context_has_shopping_list(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert "shopping_list" in resp.context
        assert "out" in resp.context["shopping_list"]
        assert "low" in resp.context["shopping_list"]

    def test_context_has_copy_text(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert "copy_text" in resp.context

    def test_empty_check_shows_tudo_ok(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert "Tudo OK" in resp.content.decode()

    def test_shopping_list_items_appear_in_response(self, operacao_client, check_with_items):
        resp = operacao_client.get(self._url(check_with_items.pk))
        content = resp.content.decode()
        assert "Açaí" in content
        assert "Banana" in content
        assert "Cupuaçu" in content

    def test_copy_text_is_empty_for_empty_check(self, operacao_client, empty_check):
        resp = operacao_client.get(self._url(empty_check.pk))
        assert resp.context["copy_text"] == ""

    def test_copy_text_is_populated_when_items_exist(self, operacao_client, check_with_items):
        resp = operacao_client.get(self._url(check_with_items.pk))
        assert resp.context["copy_text"] != ""
        assert "🔴 Acabou" in resp.context["copy_text"]
