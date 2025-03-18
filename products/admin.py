from django.contrib import admin
from .models import Product, PurchasePriceHistory

class PurchasePriceHistoryInline(admin.TabularInline):
    model = PurchasePriceHistory
    extra = 0

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'supplier', 'purchase_price', 'sale_price', 'quantity', 'status')
    list_filter = ('status', 'supplier', 'created_at')
    search_fields = ('name', 'sku', 'supplier__name')
    date_hierarchy = 'created_at'
    inlines = [PurchasePriceHistoryInline]

admin.site.register(Product, ProductAdmin)
