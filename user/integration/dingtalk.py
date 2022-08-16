import json

import requests
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.client import (OAuth2Client,
                                                           OAuth2Error)
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class DingtalkAccount(ProviderAccount):
    def get_avatar_url(self):
        return self.account.extra_data.get("avatarUrl")

    def to_str(self):
        return self.account.extra_data.get(
            "nick", super(DingtalkAccount, self).to_str()
        )


class CustomDingTalkProvider(OAuth2Provider):
    id = "custom_dingtalk"
    name = "dingtalk"
    account_class = DingtalkAccount

    def extract_uid(self, data):
        return data["openId"]

    def extract_common_fields(self, data):
        first_name, last_name = parse_name(data.get("nick", ""))
        return dict(
            username=data.get("nick"),
            name=data.get("nick"),
            first_name=first_name,
            last_name=last_name,
            email=data.get("email", None),
        )


class DingtalkOAuth2Client(OAuth2Client):
    def get_access_token(self, code):
        data = {
            "clientId": self.consumer_key,
            "clientSecret": self.consumer_secret,
            "grantType": "authorization_code",
            "code": code,
        }
        params = None
        self._strip_empty_keys(data)
        url = self.access_token_url
        if self.access_token_method == "GET":
            params = data
            data = None
        # TODO: Proper exception handling
        resp = requests.request(
            self.access_token_method,
            url,
            params=params,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        access_token = resp.json()
        if not access_token or "accessToken" not in access_token:
            raise OAuth2Error("Error retrieving access token: %s" % resp.content)
        return {
            "access_token": access_token["accessToken"],
            "refresh_token": access_token["refreshToken"],
            "expires_in": access_token["expireIn"],
        }


class CustomDingtalkOAuth2Adapter(OAuth2Adapter):
    provider_id = CustomDingTalkProvider.id

    authorize_url = "https://login.dingtalk.com/oauth2/auth"
    access_token_url = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
    user_info_url = "https://api.dingtalk.com/v1.0/contact/users/me"

    def complete_login(self, request, app, token, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "x-acs-dingtalk-access-token": token.token,
        }
        resp = requests.get(self.user_info_url, headers=headers)
        resp.raise_for_status()
        extra_data = resp.json()
        if extra_data.get("errcode", 0) != 0:
            raise OAuth2Error("Error retrieving code: %s" % resp.content)
        return self.get_provider().sociallogin_from_response(request, extra_data)


class DingtalkLogin(BaseSocialLoginView):
    adapter_class = CustomDingtalkOAuth2Adapter
    client_class = DingtalkOAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/dingtalk/redirect"

    def register_provider(self):
        providers.registry.register(CustomDingTalkProvider)

    def authorize_extra_params(self):
        return {"prompt": "consent"}


class DingtalkConnect(SocialConnectView):
    adapter_class = CustomDingtalkOAuth2Adapter
