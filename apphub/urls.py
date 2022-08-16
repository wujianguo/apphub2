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

from django.conf import settings
from django.urls import include, path, re_path

# flake8: noqa
from application.views import *
from distribute.views import *
from documentation.views import *
from organization.views import (AuthenticatedUserOrganizationList,
                                OrganizationList)
from user.views import MeUser, user_info

urlpatterns = [
    path("user", MeUser.as_view()),
    path("user/apps", AuthenticatedUserApplicationList.as_view()),
    path("user/orgs", AuthenticatedUserOrganizationList.as_view()),
    path("user/", include("user.urls")),
    path("users/<username>", user_info),
    path("download/<slug>", SlugAppDetail.as_view()),
    path("download/<slug>/packages", SlugAppPackageList.as_view()),
    path("download/<slug>/packages/latest", SlugAppPackageLatest.as_view()),
    path("download/<slug>/packages/<int:package_id>", SlugAppPackageDetail.as_view()),
    path(
        "stores/appstore/<country_code_alpha2>/<appstore_app_id>",
        AppStoreAppCurrentVersion.as_view(),
    ),
    path("stores/vivo/<vivo_store_app_id>", VivoStoreAppCurrentVersion.as_view()),
    path("stores/xiaomi/<xiaomi_store_app_id>", XiaomiStoreAppCurrentVersion.as_view()),
    path("stores/huawei", HuaweiStoreAppCurrentVersion.as_view()),
    path("stores/yingyongbao", YingyongbaoStoreAppCurrentVersion.as_view()),
    path("orgs", OrganizationList.as_view()),
    path("orgs/<org_path>/apps", OrganizationUniversalAppList.as_view()),
    path(
        "orgs/<namespace>/apps/<path>",
        OrganizationUniversalAppDetail.as_view(),
        name="org-app-detail",
    ),
    path("orgs/<namespace>/apps/<path>/icons", OrganizationUniversalAppIcon.as_view()),
    path(
        "orgs/<namespace>/apps/<path>/members",
        OrganizationUniversalAppUserList.as_view(),
    ),
    path(
        "orgs/<namespace>/apps/<path>/members/<username>",
        OrganizationUniversalAppUserDetail.as_view(),
        name="org-app-user",
    ),
    path(
        "orgs/<namespace>/apps/<path>/tokens",
        OrganizationUniversalAppTokenList.as_view(),
    ),
    path(
        "orgs/<namespace>/apps/<path>/tokens/<token_id>",
        OrganizationUniversalAppTokenDetail.as_view(),
        name="org-app-token",
    ),
    path(
        "orgs/<namespace>/apps/<path>/webhooks",
        OrganizationUniversalAppWebhookList.as_view(),
    ),
    path(
        "orgs/<namespace>/apps/<path>/webhooks/<webhook_id>",
        OrganizationUniversalAppWebhookDetail.as_view(),
        name="org-app-webhook",
    ),
    path("orgs/<namespace>/apps/<path>/packages", OrganizationAppPackageList.as_view()),
    path(
        "orgs/<namespace>/apps/<path>/packages/upload_via_file",
        OrganizationAppPackageUpload.as_view(),
    ),
    path(
        "orgs/<namespace>/apps/<path>/packages/<int:package_id>",
        OrganizationAppPackageDetail.as_view(),
        name="org-app-package",
    ),
    path(
        "orgs/<namespace>/apps/<path>/packages/<sign_name>/<sign_value>/<int:package_id>.plist",
        OrganizationAppPackagePlist.as_view(),
        name="org-app-package-plist",
    ),
    path("orgs/<namespace>/apps/<path>/releases", OrganizationAppReleaseList.as_view()),
    path(
        "orgs/<namespace>/apps/<path>/releases/<int:release_id>",
        OrganizationAppReleaseDetail.as_view(),
    ),
    path(
        "orgs/<namespace>/apps/<path>/stores/vivo", OrganizationStoreAppVivo.as_view()
    ),
    path("orgs/", include("organization.urls")),
    path("apps", VisibleUniversalAppList.as_view()),
    path("users/<username>/apps", UserUniversalAppList.as_view()),
    path(
        "users/<namespace>/apps/<path>",
        UserUniversalAppDetail.as_view(),
        name="user-app-detail",
    ),
    path("users/<namespace>/apps/<path>/icons", UserUniversalAppIcon.as_view()),
    path("users/<namespace>/apps/<path>/members", UserUniversalAppUserList.as_view()),
    path(
        "users/<namespace>/apps/<path>/members/<username>",
        UserUniversalAppUserDetail.as_view(),
        name="user-app-user",
    ),
    path("users/<namespace>/apps/<path>/tokens", UserUniversalAppTokenList.as_view()),
    path(
        "users/<namespace>/apps/<path>/tokens/<token_id>",
        UserUniversalAppTokenDetail.as_view(),
        name="user-app-token",
    ),
    path(
        "users/<namespace>/apps/<path>/webhooks", UserUniversalAppWebhookList.as_view()
    ),
    path(
        "users/<namespace>/apps/<path>/webhooks/<webhook_id>",
        UserUniversalAppWebhookDetail.as_view(),
        name="user-app-webhook",
    ),
    path("users/<namespace>/apps/<path>/packages", UserAppPackageList.as_view()),
    path(
        "users/<namespace>/apps/<path>/packages/upload_via_file",
        UserAppPackageUpload.as_view(),
    ),
    path(
        "users/<namespace>/apps/<path>/packages/<int:package_id>",
        UserAppPackageDetail.as_view(),
        name="user-app-package",
    ),
    path(
        "users/<namespace>/apps/<path>/packages/<sign_name>/<sign_value>/<int:package_id>.plist",
        UserAppPackagePlist.as_view(),
        name="user-app-package-plist",
    ),
    path("users/<namespace>/apps/<path>/releases", UserAppReleaseList.as_view()),
    path(
        "users/<namespace>/apps/<path>/releases/<int:release_id>",
        UserAppReleaseDetail.as_view(),
    ),
    path("users/<namespace>/apps/<path>/stores/vivo", UserStoreAppVivo.as_view()),
    path("upload/file", TokenAppPackageUpload.as_view()),
    path("docs/swagger.json", SwaggerJsonView.as_view()),
    path("system/", include("system.urls")),
]

if settings.ENABLE_EMAIL_ACCOUNT:
    from dj_rest_auth.registration.views import (RegisterView,
                                                 ResendEmailVerificationView,
                                                 VerifyEmailView)
    from dj_rest_auth.views import (PasswordChangeView,
                                    PasswordResetConfirmView,
                                    PasswordResetView)

    from user.views import AppHubLoginView

    urlpatterns.append(path("user/register", RegisterView.as_view()))
    urlpatterns.append(
        path(
            "user/register/verify_email",
            VerifyEmailView.as_view(),
            name="rest_verify_email",
        )
    )
    urlpatterns.append(
        path(
            "user/register/resend_email",
            ResendEmailVerificationView.as_view(),
            name="rest_resend_email",
        )
    )
    urlpatterns.append(path("user/login", AppHubLoginView.as_view(), name="rest_login"))
    urlpatterns.append(
        path(
            "user/password/reset",
            PasswordResetView.as_view(),
            name="rest_password_reset",
        )
    )
    urlpatterns.append(
        path(
            "user/password/reset/confirm",
            PasswordResetConfirmView.as_view(),
            name="rest_password_reset_confirm",
        )
    )
    urlpatterns.append(
        path(
            "user/password/change",
            PasswordChangeView.as_view(),
            name="rest_password_change",
        )
    )
if settings.SOCIAL_ACCOUNT_LIST:
    if "feishu" in settings.SOCIAL_ACCOUNT_LIST:
        from user.integration.feishu import FeishuConnect, FeishuLogin

        urlpatterns.append(
            path("user/feishu/login", FeishuLogin.as_view(), name="feishu_login")
        )
        urlpatterns.append(
            path("user/feishu/connect", FeishuConnect.as_view(), name="feishu_connect")
        )
    if "slack" in settings.SOCIAL_ACCOUNT_LIST:
        from user.integration.slack import SlackConnect, SlackLogin

        urlpatterns.append(
            path("user/slack/login", SlackLogin.as_view(), name="slack_login")
        )
        urlpatterns.append(
            path("user/slack/connect", SlackConnect.as_view(), name="slack_connect")
        )
    if "dingtalk" in settings.SOCIAL_ACCOUNT_LIST:
        from user.integration.dingtalk import DingtalkConnect, DingtalkLogin

        urlpatterns.append(
            path("user/dingtalk/login", DingtalkLogin.as_view(), name="dingtalk_login")
        )
        urlpatterns.append(
            path(
                "user/dingtalk/connect",
                DingtalkConnect.as_view(),
                name="dingtalk_connect",
            )
        )


if settings.DEFAULT_FILE_STORAGE == "storage.NginxFileStorage.NginxPrivateFileStorage":
    from storage.NginxFileStorage import nginx_media

    urlpatterns.append(
        re_path(r"^file/(?P<file>([^/]+/).*)$", nginx_media, name="file")
    )
elif settings.DEFAULT_FILE_STORAGE == "storage.AliyunOssStorage.AliyunOssMediaStorage":
    urlpatterns.append(
        path(
            "aliyun/oss/callback/<uploader_type>/<uploader_name>/<slug>",
            AliyunOssUploadPackageCallback.as_view(),
            name="aliyun-oss-callback",
        )
    )
    urlpatterns.append(
        path(
            "aliyun/oss/request_upload/<slug>",
            AliyunOssRequestUploadPackage.as_view(),
            name="aliyun-oss-request-upload",
        )
    )


if len(settings.API_URL_PREFIX) > 0:
    urlpatterns = [path(f"{settings.API_URL_PREFIX}/", include(urlpatterns))]
