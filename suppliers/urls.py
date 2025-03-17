from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier-list'),
    path('create/', views.supplier_create, name='supplier-create'),
    path('<int:pk>/', views.supplier_detail, name='supplier-detail'),
    path('<int:pk>/edit/', views.supplier_edit, name='supplier-edit'),
    path('<int:pk>/delete/', views.supplier_delete, name='supplier-delete'),
    path('debts/', views.supplier_debts, name='supplier-debts'),
]
