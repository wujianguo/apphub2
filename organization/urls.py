from django.urls import path
from organization import views

urlpatterns = [
    path('', views.OrganizationList.as_view()),
    path('<str:path>', views.OrganizationDetail.as_view(), name='org-detail'),
    path('<str:path>/icons', views.OrganizationIcon.as_view()),
    path('<str:path>/icons/<icon_name>', views.OrganizationIconDetail.as_view(), name='org-icon'),
    path('<str:path>/members', views.OrganizationUserList.as_view()),
    path('<str:path>/members/<str:username>', views.OrganizationUserDetail.as_view(), name='org-user'),
]
