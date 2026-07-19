"""
Testes da Fase 4: StockHistoryView e get_all_checks.
"""

import datetime

import pytest
from django.contrib.auth.models import Group, User
from django.utils import timezone

from stock.models import StockCheck
from stock.selectors import get_all_checks

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def operacao_user(db):
    user = User.objects.create_user(username="op4", password="pass")
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
    return User.objects.create_user(username="regular4", password="pass")


@pytest.fixture
def three_checks(db, operacao_user):
    today = timezone.localdate()
    checks = [
        StockCheck.objects.create(date=today - datetime.timedelta(days=i), created_by=operacao_user)
        for i in range(3)
    ]
    return checks


# ---------------------------------------------------------------------------
# get_all_checks selector
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetAllChecks:
    def test_returns_empty_queryset_when_no_checks(self):
        assert get_all_checks().count() == 0

    def test_returns_all_checks(self, three_checks):
        assert get_all_checks().count() == 3

    def test_ordered_most_recent_first(self, three_checks):
        dates = list(get_all_checks().values_list("date", flat=True))
        assert dates == sorted(dates, reverse=True)

    def test_select_related_created_by(self, three_checks):
        checks = list(get_all_checks())
        for check in checks:
            assert check.created_by_id is not None


# ---------------------------------------------------------------------------
# StockHistoryView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockHistoryView:
    URL = "/estoque/historico/"

    def test_requires_login(self, db):
        from django.test import Client

        resp = Client().get(self.URL)
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

    def test_context_has_checks(self, operacao_client, three_checks):
        resp = operacao_client.get(self.URL)
        assert "checks" in resp.context
        assert resp.context["checks"].count() == 3

    def test_checks_ordered_most_recent_first(self, operacao_client, three_checks):
        resp = operacao_client.get(self.URL)
        dates = [c.date for c in resp.context["checks"]]
        assert dates == sorted(dates, reverse=True)

    def test_empty_state_when_no_checks(self, operacao_client):
        resp = operacao_client.get(self.URL)
        assert "Nenhuma conferência" in resp.content.decode()

    def test_check_dates_appear_in_response(self, operacao_client, three_checks):
        resp = operacao_client.get(self.URL)
        content = resp.content.decode()
        for check in three_checks:
            assert check.date.strftime("%d/%m/%Y") in content

    def test_links_to_check_detail(self, operacao_client, three_checks):
        resp = operacao_client.get(self.URL)
        content = resp.content.decode()
        for check in three_checks:
            assert f"/estoque/{check.pk}/" in content
