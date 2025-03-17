from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, ActivityLog

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model', 'object_id', 'timestamp')
    list_filter = ('user', 'model', 'timestamp')
    search_fields = ('user__username', 'action', 'model')
    readonly_fields = ('user', 'action', 'model', 'object_id', 'timestamp')

admin.site.register(User, UserAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
