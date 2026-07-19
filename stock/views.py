from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from stock.models import StockCheck
from stock.selectors import get_active_catalog_with_status, get_all_checks, get_last_check
from stock.services import (
    build_copy_text,
    build_shopping_list,
    get_or_create_today_check,
    save_stock_check,
)


def _has_stock_permission(user):
    return user.is_superuser or user.groups.filter(name="Operacao").exists()


class StockHomeView(LoginRequiredMixin, View):
    template_name = "stock/stock_home.html"

    def get(self, request):
        if not _has_stock_permission(request.user):
            raise PermissionDenied
        return render(request, self.template_name, {"last_check": get_last_check()})


class StockCheckView(LoginRequiredMixin, View):
    template_name = "stock/stock_check.html"

    def get(self, request):
        if not _has_stock_permission(request.user):
            raise PermissionDenied

        stock_check = get_or_create_today_check(user=request.user)
        catalog = get_active_catalog_with_status(stock_check=stock_check)
        return render(request, self.template_name, {
            "stock_check": stock_check,
            "catalog": catalog,
        })

    def post(self, request):
        if not _has_stock_permission(request.user):
            raise PermissionDenied

        stock_check = get_or_create_today_check(user=request.user)

        statuses = {}
        for key, value in request.POST.items():
            if key.startswith("item_") and value in ("LOW", "OUT"):
                try:
                    statuses[int(key[5:])] = value
                except ValueError:
                    pass

        save_stock_check(stock_check=stock_check, statuses=statuses)
        messages.success(request, "Conferência salva!")
        return redirect("stock-check-detail", pk=stock_check.pk)


class StockHistoryView(LoginRequiredMixin, View):
    template_name = "stock/stock_history.html"

    def get(self, request):
        if not _has_stock_permission(request.user):
            raise PermissionDenied
        return render(request, self.template_name, {"checks": get_all_checks()})


class StockCheckDetailView(LoginRequiredMixin, View):
    template_name = "stock/stock_check_detail.html"

    def get(self, request, pk):
        if not _has_stock_permission(request.user):
            raise PermissionDenied

        stock_check = get_object_or_404(
            StockCheck.objects.select_related("created_by").prefetch_related("items"),
            pk=pk,
        )
        shopping_list = build_shopping_list(stock_check=stock_check)
        copy_text = build_copy_text(shopping_list=shopping_list)

        return render(request, self.template_name, {
            "stock_check": stock_check,
            "shopping_list": shopping_list,
            "copy_text": copy_text,
        })
