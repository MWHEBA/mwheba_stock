from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActivityLog, Notification, SystemSettings

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('phone_number', 'address', 'position', 'image', 'color_code')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات إضافية', {'fields': ('phone_number', 'address', 'position', 'image', 'color_code')}),
    )

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'model_name', 'object_id', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp', 'user')
    search_fields = ('user__username', 'description', 'model_name')
    readonly_fields = ('user', 'activity_type', 'description', 'model_name', 'object_id', 'ip_address', 'user_agent', 'timestamp')
    date_hierarchy = 'timestamp'

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'text', 'user__username')
    date_hierarchy = 'created_at'

class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'value_type', 'category', 'updated_at')
    list_filter = ('value_type', 'category')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('updated_at',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(SystemSettings, SystemSettingsAdmin)
