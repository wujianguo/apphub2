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
from django.conf import settings
from user.views import MeUser, user_avatar, user_info
from organization.views import OrganizationList
from application.views import *
from distribute.views import *
from documentation.views import *

urlpatterns = [
    path('user', MeUser.as_view()),
    path('user/apps', AuthenticatedUserApplicationList.as_view()),
    path('user/', include('user.urls')),
    path('users/<username>', user_info),
    path('users/<username>/avatar/<name>', user_avatar, name='user-avatar'),
    path('download/<slug>', SlugAppDetail.as_view()),
    path('download/<slug>/packages', SlugAppPackageList.as_view()),
    path('download/<slug>/packages/latest', SlugAppPackageLatest.as_view()),
    path('download/<slug>/packages/<int:package_id>', SlugAppPackageDetail.as_view()),
    path('orgs', OrganizationList.as_view()),
    path('orgs/<org_path>/apps', OrganizationUniversalAppList.as_view()),
    path('orgs/<namespace>/apps/<path>', OrganizationUniversalAppDetail.as_view(), name='org-app-detail'),
    path('orgs/<namespace>/apps/<path>/icons', OrganizationUniversalAppIcon.as_view()),
    path('orgs/<namespace>/apps/<path>/icons/<icon_name>', OrganizationUniversalAppIconDetail.as_view(), name='org-app-icon'),
    path('orgs/<namespace>/apps/<path>/members', OrganizationUniversalAppUserList.as_view()),
    path('orgs/<namespace>/apps/<path>/members/<username>', OrganizationUniversalAppUserDetail.as_view(), name='org-app-user'),
    path('orgs/<namespace>/apps/<path>/tokens', OrganizationUniversalAppTokenList.as_view()),
    path('orgs/<namespace>/apps/<path>/tokens/<token_id>', OrganizationUniversalAppTokenDetail.as_view(), name='org-app-token'),
    path('orgs/<namespace>/apps/<path>/webhooks', OrganizationUniversalAppWebhookList.as_view()),
    path('orgs/<namespace>/apps/<path>/webhooks/<webhook_id>', OrganizationUniversalAppWebhookDetail.as_view(), name='org-app-webhook'),
    path('orgs/<namespace>/apps/<path>/packages', OrganizationAppPackageList.as_view()),
    path('orgs/<namespace>/apps/<path>/packages/upload_via_file', OrganizationAppPackageUpload.as_view()),
    path('orgs/<namespace>/apps/<path>/packages/<int:package_id>', OrganizationAppPackageDetail.as_view(), name='org-app-package'),
    path('orgs/<namespace>/apps/<path>/packages/<int:package_id>/icons/<name>', OrganizationAppPackageIcon.as_view(), name='org-app-package-icon'),
    path('orgs/<namespace>/apps/<path>/packages/<int:package_id>/<name>', OrganizationAppPackageFile.as_view(), name='org-app-package-file'),
    path('orgs/<namespace>/apps/<path>/packages/<int:package_id>.plist', OrganizationAppPackagePlist.as_view(), name='org-app-package-plist'),
    path('orgs/<namespace>/apps/<path>/releases', OrganizationAppReleaseList.as_view()),
    path('orgs/<namespace>/apps/<path>/releases/<int:release_id>', OrganizationAppReleaseDetail.as_view()),
    path('orgs/<namespace>/apps/<path>/stores/vivo', OrganizationStoreAppVivo.as_view()),
    path('orgs/', include('organization.urls')),
    path('apps', VisibleUniversalAppList.as_view()),
    path('users/<username>/apps', UserUniversalAppList.as_view()),
    path('users/<namespace>/apps/<path>', UserUniversalAppDetail.as_view(), name='user-app-detail'),
    path('users/<namespace>/apps/<path>/icons', UserUniversalAppIcon.as_view()),
    path('users/<namespace>/apps/<path>/icons/<icon_name>', UserUniversalAppIconDetail.as_view(), name='user-app-icon'),
    path('users/<namespace>/apps/<path>/members', UserUniversalAppUserList.as_view()),
    path('users/<namespace>/apps/<path>/members/<username>', UserUniversalAppUserDetail.as_view(), name='user-app-user'),
    path('users/<namespace>/apps/<path>/tokens', UserUniversalAppTokenList.as_view()),
    path('users/<namespace>/apps/<path>/tokens/<token_id>', UserUniversalAppTokenDetail.as_view(), name='user-app-token'),
    path('users/<namespace>/apps/<path>/webhooks', UserUniversalAppWebhookList.as_view()),
    path('users/<namespace>/apps/<path>/webhooks/<webhook_id>', UserUniversalAppWebhookDetail.as_view(), name='user-app-webhook'),
    path('users/<namespace>/apps/<path>/packages', UserAppPackageList.as_view()),
    path('users/<namespace>/apps/<path>/packages/upload_via_file', UserAppPackageUpload.as_view()),
    path('users/<namespace>/apps/<path>/packages/<int:package_id>', UserAppPackageDetail.as_view(), name='user-app-package'),
    path('users/<namespace>/apps/<path>/packages/<int:package_id>/icons/<name>', UserAppPackageIcon.as_view(), name='user-app-package-icon'),
    path('users/<namespace>/apps/<path>/packages/<int:package_id>/<name>', UserAppPackageFile.as_view(), name='user-app-package-file'),
    path('users/<namespace>/apps/<path>/packages/<int:package_id>.plist', UserAppPackagePlist.as_view(), name='user-app-package-plist'),
    path('users/<namespace>/apps/<path>/releases', UserAppReleaseList.as_view()),
    path('users/<namespace>/apps/<path>/releases/<int:release_id>', UserAppReleaseDetail.as_view()),
    path('users/<namespace>/apps/<path>/stores/vivo', UserStoreAppVivo.as_view()),
    path('docs/swagger.json', SwaggerJsonView.as_view())
]

if settings.API_URL_PREFIX:
    urlpatterns = [path(f'{settings.API_URL_PREFIX}/', include(urlpatterns))]