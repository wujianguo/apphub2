from django.urls import path
from application import views

urlpatterns = [
    path('', views.UniversalAppList.as_view()),
    path('<str:path>', views.UserUniversalAppDetail.as_view(), name='app-detail'),
]
