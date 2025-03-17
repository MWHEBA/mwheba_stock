from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_notifications, name='all-notifications'),
    path('<int:notification_id>/mark-read/', views.mark_notification_read, name='mark-notification-read'),
    path('mark-all-read/', views.mark_all_read, name='mark-all-read'),
]
