"""
Testes das views do app stock (Fase 2).
"""

import pytest
from django.contrib.auth.models import Group, User
from django.utils import timezone

from stock.models import StockCategory, StockCheck, StockCheckItem, StockItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def operacao_user(db):
    user = User.objects.create_user(username="op_user", password="pass")
    group, _ = Group.objects.get_or_create(name="Operacao")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="regular", password="pass")


@pytest.fixture
def superuser(db):
    return User.objects.create_user(username="admin", password="pass", is_superuser=True)


@pytest.fixture
def operacao_client(operacao_user):
    from django.test import Client
    c = Client()
    c.force_login(operacao_user)
    return c


@pytest.fixture
def superuser_client(superuser):
    from django.test import Client
    c = Client()
    c.force_login(superuser)
    return c


@pytest.fixture
def anon_client(db):
    from django.test import Client
    return Client()


@pytest.fixture
def category(db):
    return StockCategory.objects.create(name="Frutas", sort_order=1, active=True)


@pytest.fixture
def item(db, category):
    return StockItem.objects.create(category=category, name="Banana", sort_order=1, active=True)


# ---------------------------------------------------------------------------
# StockHomeView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockHomeView:
    URL = "/estoque/"

    def test_requires_login(self, anon_client):
        resp = anon_client.get(self.URL)
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]

    def test_denies_user_without_permission(self, regular_user):
        from django.test import Client
        c = Client()
        c.force_login(regular_user)
        resp = c.get(self.URL)
        assert resp.status_code == 403

    def test_accessible_for_operacao(self, operacao_client):
        resp = operacao_client.get(self.URL)
        assert resp.status_code == 200

    def test_accessible_for_superuser(self, superuser_client):
        resp = superuser_client.get(self.URL)
        assert resp.status_code == 200

    def test_shows_last_check_when_exists(self, operacao_client, operacao_user):
        check = StockCheck.objects.create(
            date=timezone.localdate(), created_by=operacao_user
        )
        resp = operacao_client.get(self.URL)
        assert resp.status_code == 200
        assert resp.context["last_check"].pk == check.pk

    def test_last_check_is_none_when_no_checks(self, operacao_client):
        resp = operacao_client.get(self.URL)
        assert resp.context["last_check"] is None


# ---------------------------------------------------------------------------
# StockCheckView — GET
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCheckViewGet:
    URL = "/estoque/conferir/"

    def test_requires_login(self, anon_client):
        resp = anon_client.get(self.URL)
        assert resp.status_code == 302

    def test_denies_user_without_permission(self, regular_user):
        from django.test import Client
        c = Client()
        c.force_login(regular_user)
        resp = c.get(self.URL)
        assert resp.status_code == 403

    def test_accessible_for_operacao(self, operacao_client, item):
        resp = operacao_client.get(self.URL)
        assert resp.status_code == 200

    def test_creates_today_check_on_get(self, operacao_client, item):
        assert StockCheck.objects.count() == 0
        operacao_client.get(self.URL)
        assert StockCheck.objects.filter(date=timezone.localdate()).count() == 1

    def test_does_not_duplicate_check_on_multiple_gets(self, operacao_client, item):
        operacao_client.get(self.URL)
        operacao_client.get(self.URL)
        assert StockCheck.objects.count() == 1

    def test_catalog_in_context(self, operacao_client, item):
        resp = operacao_client.get(self.URL)
        assert "catalog" in resp.context
        assert len(resp.context["catalog"]) == 1
        assert resp.context["catalog"][0]["category"].name == "Frutas"

    def test_items_default_to_ok(self, operacao_client, item):
        resp = operacao_client.get(self.URL)
        items = resp.context["catalog"][0]["items"]
        assert items[0].current_status == "OK"

    def test_marked_items_show_correct_status(self, operacao_client, operacao_user, item):
        check = StockCheck.objects.create(date=timezone.localdate(), created_by=operacao_user)
        StockCheckItem.objects.create(
            stock_check=check, item=item, item_name=item.name, status="OUT"
        )
        resp = operacao_client.get(self.URL)
        items = resp.context["catalog"][0]["items"]
        assert items[0].current_status == "OUT"


# ---------------------------------------------------------------------------
# StockCheckView — POST
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockCheckViewPost:
    URL = "/estoque/conferir/"

    def test_post_requires_login(self, anon_client):
        resp = anon_client.post(self.URL, {})
        assert resp.status_code == 302

    def test_post_denies_without_permission(self, regular_user):
        from django.test import Client
        c = Client()
        c.force_login(regular_user)
        resp = c.post(self.URL, {})
        assert resp.status_code == 403

    def test_post_saves_low_item(self, operacao_client, item):
        operacao_client.post(self.URL, {f"item_{item.pk}": "LOW"})
        check = StockCheck.objects.get(date=timezone.localdate())
        assert check.items.filter(item=item, status="LOW").exists()

    def test_post_saves_out_item(self, operacao_client, item):
        operacao_client.post(self.URL, {f"item_{item.pk}": "OUT"})
        check = StockCheck.objects.get(date=timezone.localdate())
        assert check.items.filter(item=item, status="OUT").exists()

    def test_post_ok_does_not_create_item(self, operacao_client, item):
        operacao_client.post(self.URL, {f"item_{item.pk}": "OK"})
        check = StockCheck.objects.get(date=timezone.localdate())
        assert check.items.count() == 0

    def test_post_redirects_to_check_detail(self, operacao_client, item):
        resp = operacao_client.post(self.URL, {f"item_{item.pk}": "OUT"})
        assert resp.status_code == 302
        check = StockCheck.objects.get(date=timezone.localdate())
        assert resp["Location"] == f"/estoque/{check.pk}/"

    def test_post_creates_check_if_not_exists(self, operacao_client, item):
        assert StockCheck.objects.count() == 0
        operacao_client.post(self.URL, {f"item_{item.pk}": "OUT"})
        assert StockCheck.objects.count() == 1
