from django.contrib import admin
from .models import Customer, CustomerCategory

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'address', 'debt', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'created_at'

class CustomerCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code', 'description')
    search_fields = ('name',)

admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerCategory, CustomerCategoryAdmin)
