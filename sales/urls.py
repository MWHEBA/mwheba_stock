from django.urls import path
from . import views

urlpatterns = [
    path('', views.sale_list, name='sale-list'),
    path('create/', views.sale_create, name='sale-create'),
    path('<int:pk>/', views.sale_detail, name='sale-detail'),
    path('<int:pk>/edit/', views.sale_edit, name='sale-edit'),
    path('<int:pk>/delete/', views.sale_delete, name='sale-delete'),
    path('<int:pk>/print/', views.sale_print, name='sale-print'),
    path('payments/', views.customer_payments, name='customer-payments'),
]
