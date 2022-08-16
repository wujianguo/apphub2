from allauth.socialaccount import providers
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.slack.views import (SlackOAuth2Adapter,
                                                         SlackProvider)
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class CustomSlackProvider(SlackProvider):
    id = "custom_slack"

    def extract_common_fields(self, data):
        ret = super().extract_common_fields(data)
        first_name, last_name = parse_name(ret.get("name", ""))
        ret["first_name"] = first_name
        ret["last_name"] = last_name
        return ret


class CustomSlackOAuth2Adapter(SlackOAuth2Adapter):
    provider_id = CustomSlackProvider.id


class SlackLogin(BaseSocialLoginView):
    adapter_class = CustomSlackOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/slack/redirect"

    def register_provider(self):
        providers.registry.register(CustomSlackProvider)


class SlackConnect(SocialConnectView):
    adapter_class = SlackOAuth2Adapter
