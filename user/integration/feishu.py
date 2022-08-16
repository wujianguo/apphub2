from allauth.socialaccount import providers
from allauth.socialaccount.providers.feishu.client import FeishuOAuth2Client
from allauth.socialaccount.providers.feishu.provider import FeishuProvider
from allauth.socialaccount.providers.feishu.views import FeishuOAuth2Adapter
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class CustomFeishuProvider(FeishuProvider):
    id = "custom_feishu"

    def extract_common_fields(self, data):
        first_name, last_name = parse_name(data.get("name", ""))
        return dict(
            username=data.get("name"),
            name=data.get("name"),
            first_name=first_name,
            last_name=last_name,
            email=data.get("email", None),
        )


class CustomFeishuOAuth2Adapter(FeishuOAuth2Adapter):
    provider_id = CustomFeishuProvider.id


class FeishuLogin(BaseSocialLoginView):
    adapter_class = CustomFeishuOAuth2Adapter
    client_class = FeishuOAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/feishu/redirect"

    def register_provider(self):
        providers.registry.register(CustomFeishuProvider)


class FeishuConnect(SocialConnectView):
    adapter_class = FeishuOAuth2Adapter
