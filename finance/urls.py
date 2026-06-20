"""
URLs da aplicação finance.
"""

from django.urls import path
from finance import views

urlpatterns = [
    # Expenses
    path('expenses/', views.ExpenseListView.as_view(), name='expense-list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense-edit'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense-delete'),

    # Daily Closings
    path('closings/', views.DailyClosingListView.as_view(), name='closing-list'),
    path('closings/create/', views.DailyClosingCreateView.as_view(), name='closing-create'),
    path('closings/<int:pk>/edit/', views.DailyClosingUpdateView.as_view(), name='closing-edit'),
    path('closings/<int:pk>/delete/', views.DailyClosingDeleteView.as_view(), name='closing-delete'),
]
