from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product-list'),
    path('create/', views.product_create, name='product-create'),
    path('<int:pk>/', views.product_detail, name='product-detail'),
    path('<int:pk>/edit/', views.product_edit, name='product-edit'),
    path('<int:pk>/delete/', views.product_delete, name='product-delete'),
    path('categories/', views.product_categories, name='product-categories'),
]
