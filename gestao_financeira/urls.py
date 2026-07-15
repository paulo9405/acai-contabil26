"""
URL configuration for gestao_financeira project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('finance.urls')),
    path('', include('orders.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
]
