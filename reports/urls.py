from django.urls import path
from . import views

urlpatterns = [
    path('financial/', views.financial_report, name='financial-report'),
    path('sales/', views.sales_report, name='sales-report'),
    path('inventory/', views.inventory_report, name='inventory-report'),
    path('profit/', views.profit_report, name='profit-report'),
    path('inventory-analysis/', views.inventory_analysis, name='inventory-analysis'),
    path('debts/', views.debts_report, name='debts-report'),
]
