from django.urls import path

from stock.views import StockCheckDetailView, StockCheckView, StockHomeView

urlpatterns = [
    path("estoque/", StockHomeView.as_view(), name="stock-home"),
    path("estoque/conferir/", StockCheckView.as_view(), name="stock-check"),
    path("estoque/<int:pk>/", StockCheckDetailView.as_view(), name="stock-check-detail"),
]
