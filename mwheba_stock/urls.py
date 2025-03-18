from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Define all URLs in English for consistency
urlpatterns = [
    path('admin/', admin.site.urls),
    # Core app URLs (including login, dashboard, etc.)
    path('', include('accounts.urls')),
    
    # Main app sections
    path('products/', include('products.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('store_settings.urls')),  # Only using store_settings
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
