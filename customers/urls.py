from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer-list'),
    path('create/', views.customer_create, name='customer-create'),
    path('<int:pk>/', views.customer_detail, name='customer-detail'),
    path('<int:pk>/edit/', views.customer_edit, name='customer-edit'),
    path('<int:pk>/delete/', views.customer_delete, name='customer-delete'),
    path('<int:pk>/record-payment/', views.record_payment, name='add-customer-payment'),
    path('debts/', views.customer_debts, name='customer-debts'),
    # إدارة تصنيفات العملاء
    path('categories/create/', views.category_create_ajax, name='category-create-ajax'),
    path('categories/', views.category_list, name='customer-categories'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category-delete'),
]
