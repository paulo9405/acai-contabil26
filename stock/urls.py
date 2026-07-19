from django.urls import path

from stock.views import StockCheckDetailView, StockCheckView, StockHistoryView, StockHomeView

urlpatterns = [
    path("estoque/", StockHomeView.as_view(), name="stock-home"),
    path("estoque/conferir/", StockCheckView.as_view(), name="stock-check"),
    path("estoque/historico/", StockHistoryView.as_view(), name="stock-history"),
    path("estoque/<int:pk>/", StockCheckDetailView.as_view(), name="stock-check-detail"),
]
