from django.contrib import admin
from .models import Supplier, SupplierCategory

@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code', 'created_at')
    search_fields = ('name',)
    list_filter = ('color_code',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'category', 'balance', 'status')
    list_filter = ('status', 'category', 'is_preferred')
    search_fields = ('name', 'code', 'phone', 'email')
    readonly_fields = ('code', 'created_at', 'updated_at')
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'code', 'phone', 'alternative_phone', 'email', 'address', 'status')
        }),
        ('التصنيف والمعلومات الإضافية', {
            'fields': ('category', 'is_preferred', 'tax_number', 'payment_terms', 'notes')
        }),
        ('البيانات المالية', {
            'fields': ('credit_limit', 'balance', 'total_purchases')
        }),
        ('البيانات الزمنية', {
            'fields': ('created_at', 'updated_at', 'last_purchase_date')
        }),
    )
