from django.contrib.auth.views import (
    LogoutView, PasswordChangeView, LoginView,
    PasswordChangeDoneView, PasswordResetView,
    PasswordResetDoneView
)
from django.urls import path

from . import views


app_name = 'users'


urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/',
         LoginView.as_view(template_name='users/login.html'),
         name='login'),
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path(
        'password_change_form/',
        PasswordChangeView.as_view(
            template_name='users/password_change_form.html'),
        name='password_change_form'),
    path(
        'password_change_done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'),
    path(
        'password_reset_form',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html'),
        name='password_reset_form'),
    path(
        'password_reset_done/done',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done')
]
