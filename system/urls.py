from django.urls import path

from system import views

urlpatterns = [path("info", views.info_api), path("current", views.current)]
