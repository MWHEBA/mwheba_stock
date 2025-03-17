from django.urls import path
from . import views

urlpatterns = [
    path('general/', views.general_settings, name='general-settings'),
    path('system/', views.system_settings, name='system-settings'),
    path('users/', views.users_list, name='users-list'),
    path('users/create/', views.user_create, name='user-create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user-edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user-delete'),
    path('users/<int:user_id>/activate/', views.user_activate, name='user-activate'),
    path('users/<int:user_id>/deactivate/', views.user_deactivate, name='user-deactivate'),
    path('users/<int:user_id>/reset-password/', views.user_reset_password, name='user-reset-password'),
    path('categories/', views.categories, name='categories'),
    path('categories/create/', views.category_create, name='category-create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category-edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category-delete'),
    path('tax/', views.tax_settings, name='tax-settings'),
    path('tax/general/', views.tax_general_settings, name='tax-general-settings'),
    path('tax/class/create/', views.tax_class_create, name='tax-class-create'),
    path('backup-restore/', views.backup_restore, name='backup-restore'),
    path('backup-restore/create/', views.create_backup, name='create-backup'),
    path('backup-restore/<int:backup_id>/download/', views.download_backup, name='download-backup'),
    path('backup-restore/<int:backup_id>/restore/', views.restore_backup, name='restore-backup'),
    path('backup-restore/<int:backup_id>/delete/', views.delete_backup, name='delete-backup'),
    path('backup-restore/restore/upload/', views.restore_backup_upload, name='restore-backup-upload'),
]
