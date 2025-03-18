from django.contrib import admin
from .models import Supplier

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'address', 'debt', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'phone', 'email')
    date_hierarchy = 'created_at'

admin.site.register(Supplier, SupplierAdmin)
