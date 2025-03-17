from django.urls import path
from django.views.i18n import set_language
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('activity-log/', views.activity_log, name='activity-log'),
    path('set-language/', set_language, name='set_language'),
    path('profile/edit/', views.profile_edit, name='profile-edit'),
    path('profile/picture/update/', views.profile_picture_update, name='profile-picture-update'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/profile/'
    ), name='password-change'),
]
