from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.ips_list, name='ips_list'),
    path('new/', views.ips_create, name='ips_create'),
    path('<int:pk>/', views.ips_detail, name='ips_detail'),
    path('<int:pk>/edit/', views.ips_edit, name='ips_edit'),
    path('<int:pk>/portfolio/', views.ips_portfolio, name='ips_portfolio'),
]

# Mounted under /accounts/ in config/urls.py.
account_urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='ips/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='ips/password_reset_form.html',
        email_template_name='ips/password_reset_email.txt'), name='password_reset'),
    path('password-reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='ips/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='ips/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='ips/password_reset_complete.html'), name='password_reset_complete'),
]
