from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('store_settings.urls')),  # Only using store_settings
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
