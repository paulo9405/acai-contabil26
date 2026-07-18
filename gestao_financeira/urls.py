"""
URL configuration for gestao_financeira project.
"""

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import include, path


@login_required
def home_redirect(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    return redirect("order-list")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("finance.urls")),
    path("", include("orders.urls")),
    path("", home_redirect, name="home"),
]
