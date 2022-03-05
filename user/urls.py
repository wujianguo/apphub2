from django.urls import path
from user import views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout_user)
]
