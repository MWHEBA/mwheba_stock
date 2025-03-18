from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier-list'),
    path('create/', views.supplier_create, name='supplier-create'),
    path('<int:pk>/', views.supplier_detail, name='supplier-detail'),
    path('<int:pk>/edit/', views.supplier_edit, name='supplier-update'),
    path('<int:pk>/delete/', views.supplier_delete, name='supplier-delete'),
    path('<int:pk>/record-payment/', views.record_payment, name='supplier-payment'),
    path('<int:pk>/modal-detail/', views.supplier_modal_detail, name='supplier-modal-detail'),
    path('<int:pk>/modal-edit/', views.supplier_modal_edit, name='supplier-modal-edit'),
    path('<int:pk>/payment-form/', views.supplier_payment_form, name='supplier-payment-form'),
    path('<int:pk>/get-data/', views.get_supplier_data, name='get-supplier-data'),
    
    # المسارات الجديدة
    path('debts/', views.supplier_debts, name='supplier-debts'),
    path('categories/', views.supplier_categories, name='supplier-categories'),
    path('categories/create/', views.supplier_category_create, name='supplier-category-create'),
    path('categories/<int:pk>/edit/', views.supplier_category_edit, name='supplier-category-edit'),
    path('categories/<int:pk>/delete/', views.supplier_category_delete, name='supplier-category-delete'),
]
