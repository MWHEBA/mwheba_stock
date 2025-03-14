"""
URL configuration for mwheba_stock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views

from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),  # Root URL
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),  # Include inventory URLs
    path('logout/', LogoutView.as_view(), name='logout'),  # ✅ Correct logout setup
    
    # API endpoints for orders
    path('api/orders/<int:order_id>/details/', views.order_details_api, name='order_details_api'),
    path('api/orders/<int:order_id>/delete/', views.order_delete_api, name='order_delete_api'),
    path('api/orders/<int:order_id>/update/', views.update_order_api, name='update_order_api'),
    path('api/orders/create/', views.create_order, name='create_order_api'),
    
    # API endpoints for purchase orders
    path('api/purchase-orders/<int:purchase_order_id>/details/', views.get_purchase_order_details, name='purchase_order_details_api'),
    path('api/purchase-orders/<int:purchase_order_id>/delete/', views.delete_purchase_order, name='purchase_order_delete_api'),
    path('api/purchase-orders/<int:purchase_order_id>/update/', views.update_purchase_order, name='purchase_order_update_api'),
    path('api/purchase-orders/create/', views.create_purchase_order, name='create_purchase_order_api'),
    
    # API endpoints for products and suppliers
    path('api/products/', views.get_products, name='get_products_api'),
    path('api/products/create/', views.create_product, name='create_product_api'),
    path('api/suppliers/create/', views.create_supplier, name='create_supplier_api'),
]

# Add media file handling in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
