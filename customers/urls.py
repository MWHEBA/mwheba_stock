from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer-list'),
    path('create/', views.customer_create, name='customer-create'),
    path('<int:pk>/', views.customer_detail, name='customer-detail'),
    path('<int:pk>/edit/', views.customer_edit, name='customer-edit'),
    path('<int:pk>/delete/', views.customer_delete, name='customer-delete'),
    path('<int:pk>/record-payment/', views.record_payment, name='record-payment'),
    path('debts/', views.customer_debts, name='customer-debts'),
    path('categories/', views.customer_categories, name='customer-categories'),
    path('categories/create/', views.customer_category_create, name='customer-category-create'),
    path('categories/<int:pk>/edit/', views.customer_category_edit, name='customer-category-edit'),
    path('categories/<int:pk>/delete/', views.customer_category_delete, name='customer-category-delete'),
    
    # مسارات إضافية للمودالات
    path('<int:pk>/get-data/', views.get_customer_data, name='get-customer-data'),
]
