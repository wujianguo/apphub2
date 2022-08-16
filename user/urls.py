from django.urls import path

from user import views

urlpatterns = [
    path("auth/config", views.auth_config),
    path("logout", views.AppHubLogoutView.as_view(), name="rest_logout"),
    path("avatar", views.UserAvatar.as_view()),
]
