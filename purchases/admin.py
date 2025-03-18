from django.contrib import admin
from .models import Purchase, PurchaseItem, Payment

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'total_price', 'status', 'created_by')
    list_filter = ('status', 'order_date', 'created_at')
    search_fields = ('supplier__name', 'id')
    date_hierarchy = 'order_date'
    inlines = [PurchaseItemInline, PaymentInline]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'purchase', 'amount', 'payment_date', 'created_by')
    list_filter = ('payment_date',)
    search_fields = ('supplier__name', 'notes')
    date_hierarchy = 'payment_date'

admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Payment, PaymentAdmin)
