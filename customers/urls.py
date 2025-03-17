from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer-list'),
    path('create/', views.customer_create, name='customer-create'),
    path('<int:pk>/', views.customer_detail, name='customer-detail'),
    path('<int:pk>/edit/', views.customer_edit, name='customer-edit'),
    path('<int:pk>/delete/', views.customer_delete, name='customer-delete'),
    path('debts/', views.customer_debts, name='customer-debts'),
]
