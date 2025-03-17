from django.urls import path
from . import views

urlpatterns = [
    path('', views.purchase_list, name='purchase-list'),
    path('create/', views.purchase_create, name='purchase-create'),
    path('<int:pk>/', views.purchase_detail, name='purchase-detail'),
    path('<int:pk>/edit/', views.purchase_edit, name='purchase-edit'),
    path('<int:pk>/delete/', views.purchase_delete, name='purchase-delete'),
    path('payments/', views.purchase_payments, name='purchase-payments'),
]
