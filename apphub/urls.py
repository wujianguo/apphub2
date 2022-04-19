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
from user.views import MeUser
from organization.views import OrganizationList
from application.views import *
from distribute.views import *
from documentation.views import *

urlpatterns = [
    path('api/user', MeUser.as_view()),
    path('api/user/apps', AuthenticatedUserApplicationList.as_view()),
    path('api/user/', include('user.urls')),
    path('api/orgs', OrganizationList.as_view()),
    path('api/orgs/<org_path>/apps', OrganizationUniversalAppList.as_view()),
    path('api/orgs/<namespace>/apps/<path>', OrganizationUniversalAppDetail.as_view(), name='org-app-detail'),
    path('api/orgs/<namespace>/apps/<path>/icons', OrganizationUniversalAppIcon.as_view()),
    path('api/orgs/<namespace>/apps/<path>/icons/<icon_name>', OrganizationUniversalAppIconDetail.as_view(), name='org-app-icon'),
    path('api/orgs/<namespace>/apps/<path>/members', OrganizationUniversalAppUserList.as_view()),
    path('api/orgs/<namespace>/apps/<path>/members/<username>', OrganizationUniversalAppUserDetail.as_view(), name='org-app-user'),
    path('api/orgs/<namespace>/apps/<path>/tokens', OrganizationUniversalAppTokenList.as_view()),
    path('api/orgs/<namespace>/apps/<path>/tokens/<token_id>', OrganizationUniversalAppTokenDetail.as_view(), name='org-app-token'),
    path('api/orgs/<namespace>/apps/<path>/webhooks', OrganizationUniversalAppWebhookList.as_view()),
    path('api/orgs/<namespace>/apps/<path>/webhooks/<webhook_id>', OrganizationUniversalAppWebhookDetail.as_view(), name='org-app-webhook'),
    path('api/orgs/<namespace>/apps/<path>/packages', OrganizationAppPackageList.as_view()),
    path('api/orgs/<namespace>/apps/<path>/packages/<int:package_id>', OrganizationAppPackageDetail.as_view()),
    path('api/orgs/<namespace>/apps/<path>/releases', OrganizationAppReleaseList.as_view()),
    path('api/orgs/<namespace>/apps/<path>/releases/<int:release_id>', OrganizationAppReleaseDetail.as_view()),
    path('api/orgs/<namespace>/apps/<path>/stores/vivo', OrganizationStoreAppVivo.as_view()),
    path('api/orgs/', include('organization.urls')),
    path('api/apps', VisibleUniversalAppList.as_view()),
    path('api/users/<username>/apps', UserUniversalAppList.as_view()),
    path('api/users/<namespace>/apps/<path>', UserUniversalAppDetail.as_view(), name='user-app-detail'),
    path('api/users/<namespace>/apps/<path>/icons', UserUniversalAppIcon.as_view()),
    path('api/users/<namespace>/apps/<path>/icons/<icon_name>', UserUniversalAppIconDetail.as_view(), name='user-app-icon'),
    path('api/users/<namespace>/apps/<path>/members', UserUniversalAppUserList.as_view()),
    path('api/users/<namespace>/apps/<path>/members/<username>', UserUniversalAppUserDetail.as_view(), name='user-app-user'),
    path('api/users/<namespace>/apps/<path>/tokens', UserUniversalAppTokenList.as_view()),
    path('api/users/<namespace>/apps/<path>/tokens/<token_id>', UserUniversalAppTokenDetail.as_view(), name='user-app-token'),
    path('api/users/<namespace>/apps/<path>/webhooks', UserUniversalAppWebhookList.as_view()),
    path('api/users/<namespace>/apps/<path>/webhooks/<webhook_id>', UserUniversalAppWebhookDetail.as_view(), name='user-app-webhook'),
    path('api/users/<namespace>/apps/<path>/packages', UserAppPackageList.as_view()),
    path('api/users/<namespace>/apps/<path>/packages/<int:package_id>', UserAppPackageDetail.as_view()),
    path('api/users/<namespace>/apps/<path>/releases', UserAppReleaseList.as_view()),
    path('api/users/<namespace>/apps/<path>/releases/<int:release_id>', UserAppReleaseDetail.as_view()),
    path('api/users/<namespace>/apps/<path>/stores/vivo', UserStoreAppVivo.as_view()),
    path('api/docs/swagger.json', SwaggerJsonView.as_view())
]
