from django.urls import path
from user import views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout_user),
    path('email/request_verify', views.request_verify_email),
    path('email/verify', views.verify_email),
    path('password/change', views.change_password),
    path('password/request_reset', views.request_reset_password),
    path('password/reset', views.reset_password),
    path('avatar', views.UserAvatar.as_view()),
    path('<username>', views.user_info)
]
