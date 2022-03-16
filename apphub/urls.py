"""apphub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path
from user.views import me
from organization.views import OrganizationList
from application.views import UniversalAppList, UserUniversalAppDetail, OrganizationUniversalAppList, OrganizationUniversalAppDetail
from distribute.views import UserAppPackageList, UserAppPackageDetail, UserAppReleaseList, UserAppReleaseDetail, UserStoreAppVivo

urlpatterns = [
    path('api/user', me),
    path('api/user/', include('user.urls')),
    path('api/orgs', OrganizationList.as_view()),
    path('api/orgs/<org_path>/apps', OrganizationUniversalAppList.as_view()),
    path('api/orgs/<org_path>/apps/<app_path>', OrganizationUniversalAppDetail.as_view()),
    path('api/orgs/', include('organization.urls')),
    path('api/apps', UniversalAppList.as_view()),
    path('api/users/<username>/apps/<path>', UserUniversalAppDetail.as_view(), name='app-detail'),
    path('api/users/<username>/apps/<path>/packages', UserAppPackageList.as_view()),
    path('api/users/<username>/apps/<path>/packages/<int:internal_build>', UserAppPackageDetail.as_view()),
    path('api/users/<username>/apps/<path>/releases/<int:release_id>', UserAppReleaseDetail.as_view()),
    path('api/users/<username>/apps/<path>/releases/<str:environment>', UserAppReleaseList.as_view()),
    path('api/users/<username>/apps/<path>/stores/vivo', UserStoreAppVivo.as_view()),
]
