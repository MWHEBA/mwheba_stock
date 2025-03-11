from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import product_list
from core.views import order_list
from core.views import purchase_order_list
from core import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Reports
    path('report/', views.stock_report, name='stock_report'),
    path('sales_report/', views.sales_report, name='sales_report'),
    path('profit_loss_report/', views.profit_loss_report, name='profit_loss_report'),
    path('stock_movement_report/', views.stock_movement_report, name='stock_movement_report'),
    
    # Export Reports
    path('export_stock_report/', views.export_stock_report, name='export_stock_report'),
    path('export_sales_report/', views.export_sales_report, name='export_sales_report'),
    path('export_profit_loss_report/', views.export_profit_loss_report, name='export_profit_loss_report'),
    path('export_stock_movement_report/', views.export_stock_movement_report, name='export_stock_movement_report'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('supplier/create/', views.create_supplier, name='create_supplier'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('client/create/', views.create_client, name='create_client'),
    
    # Client API endpoints
    path('api/clients/create/', views.create_client, name='create_client_api'),
    path('api/clients/<int:client_id>/update/', views.update_client, name='update_client'),
    path('api/clients/<int:client_id>/details/', views.get_client_details, name='get_client_details'),
    path('api/clients/<int:client_id>/delete/', views.delete_client, name='delete_client'),

    # Products
    path('products/', product_list, name='product_list'),
    
    # Product API endpoints
    path('api/products/create/', views.create_product, name='create_product'),
    path('api/products/<int:product_id>/update/', views.update_product, name='update_product'),
    path('api/products/<int:product_id>/details/', views.get_product_details, name='get_product_details'),
    path('api/products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    
    # Category, Supplier, and Location API endpoints
    path('api/categories/create/', views.create_category, name='create_category'),
    path('api/suppliers/create/', views.create_supplier, name='create_supplier'),
    path('api/suppliers/<int:supplier_id>/update/', views.update_supplier, name='update_supplier'),
    path('api/suppliers/<int:supplier_id>/details/', views.get_supplier_details, name='get_supplier_details'),
    path('api/suppliers/<int:supplier_id>/delete/', views.delete_supplier, name='delete_supplier'),
    path('api/locations/create/', views.create_location, name='create_location'),

    # Orders
    path('orders/', order_list, name='order_list'),
    path('orders/<int:order_id>/', views.get_order_details, name='order_detail'),

    # Purchase Orders
    path('purchase-orders/', purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/<int:purchase_order_id>/', views.get_purchase_order_details, name='purchase_order_detail'),
    
    # AJAX endpoints for Orders
    path('api/orders/create/', views.create_order, name='create_order'),
    path('api/orders/<int:order_id>/update/', views.update_order, name='update_order'),
    path('api/orders/<int:order_id>/details/', views.get_order_details, name='get_order_details'),
    path('api/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    
    # AJAX endpoints for Purchase Orders
    path('api/purchase-orders/create/', views.create_purchase_order, name='create_purchase_order'),
    path('api/purchase-orders/<int:purchase_order_id>/update/', views.update_purchase_order, name='update_purchase_order'),
    path('api/purchase-orders/<int:purchase_order_id>/details/', views.get_purchase_order_details, name='get_purchase_order_details'),
    path('api/purchase-orders/<int:purchase_order_id>/delete/', views.delete_purchase_order, name='delete_purchase_order'),

]
