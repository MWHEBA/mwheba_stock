from django.contrib import admin
from .models import Sale, SaleItem, CustomerPayment

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

class CustomerPaymentInline(admin.TabularInline):
    model = CustomerPayment
    extra = 0

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'sale_date', 'total_price', 'status', 'created_by')
    list_filter = ('status', 'sale_date', 'created_at')
    search_fields = ('customer__name', 'id')
    date_hierarchy = 'sale_date'
    inlines = [SaleItemInline, CustomerPaymentInline]

class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'sale', 'amount', 'payment_date', 'created_by')
    list_filter = ('payment_date',)
    search_fields = ('customer__name', 'notes')
    date_hierarchy = 'payment_date'

admin.site.register(Sale, SaleAdmin)
admin.site.register(CustomerPayment, CustomerPaymentAdmin)
