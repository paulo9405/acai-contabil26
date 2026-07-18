"""
URLs da aplicação finance.
"""

from django.urls import path

from finance import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # Reports
    path("reports/", views.ReportView.as_view(), name="reports"),
    # Fechamento do Dia — tela unificada (nova arquitetura)
    path("fechamento/", views.DailyClosingTodayRedirectView.as_view(), name="daily-closing-today"),
    path(
        "fechamento/<str:closing_date>/",
        views.DailyClosingUnifiedView.as_view(),
        name="daily-closing",
    ),
    # Expenses (rotas legadas — mantidas para compatibilidade)
    path("expenses/", views.ExpenseListView.as_view(), name="expense-list"),
    path("expenses/create/", views.ExpenseCreateView.as_view(), name="expense-create"),
    path("expenses/<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="expense-edit"),
    path("expenses/<int:pk>/delete/", views.ExpenseDeleteView.as_view(), name="expense-delete"),
    # Daily Closings (rotas legadas — mantidas para compatibilidade)
    path("closings/", views.DailyClosingListView.as_view(), name="closing-list"),
    path("closings/create/", views.DailyClosingCreateView.as_view(), name="closing-create"),
    path("closings/<int:pk>/edit/", views.DailyClosingUpdateView.as_view(), name="closing-edit"),
    path(
        "closings/<int:pk>/delete/", views.DailyClosingDeleteView.as_view(), name="closing-delete"
    ),
]
