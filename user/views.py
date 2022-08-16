import shutil
import tempfile

import requests
from allauth.account.signals import user_signed_up
from dj_rest_auth.views import LoginView, LogoutView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.dispatch import receiver
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from user.serializers import (UserAvatarSerializer, UserSerializer,
                              UserUpdateSerializer)
from util.image import generate_icon_image
from util.url import build_absolute_uri, build_static_uri

UserModel = get_user_model()


@receiver(user_signed_up)
def handle_user_signed_up(sender, **kwargs):
    user = kwargs.get("user")
    sociallogin = kwargs.get("sociallogin", None)
    if sociallogin:
        avatar_url = sociallogin.account.get_avatar_url()
        if avatar_url:
            with requests.get(avatar_url, stream=True) as f:
                tmpf = tempfile.TemporaryFile()
                shutil.copyfileobj(f.raw, tmpf)
                tmpf.seek(0)
                user.avatar.save("avatar.png", File(tmpf))
                tmpf.close()
                return

    file = generate_icon_image(user.first_name if user.first_name else user.username)
    user.avatar.save("avatar.png", File(file.file))


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def auth_config(request):
    data = {}
    if settings.ENABLE_EMAIL_ACCOUNT:
        data["email"] = {"enable": True}
        if settings.ACCOUNT_EMAIL_DOMAIN:
            data["email"]["domain"] = settings.ACCOUNT_EMAIL_DOMAIN
    if settings.SOCIAL_ACCOUNT_LIST:
        social = []
        for item in settings.SOCIAL_ACCOUNT_LIST:
            key = "custom_" + item
            app = settings.SOCIALACCOUNT_PROVIDERS.get(key, None)
            if not app:
                continue
            social.append(
                {
                    "type": item,
                    "name": app.get("display_name", item),
                    "logo": build_static_uri("integrations/" + item + ".png"),
                    "auth_url": settings.EXTERNAL_API_URL + "/user/" + item + "/login",
                }
            )
        data["social"] = social
    return Response(data)


class AppHubLoginView(LoginView):
    def get_response(self):
        if self.token:
            response_serializer = UserSerializer(self.user)
            response_data = response_serializer.data
            response_data["token"] = self.token.key
            return Response(response_data, status=status.HTTP_200_OK)
        return super().get_response()


class AppHubLogoutView(LogoutView):
    def delete(self, request):
        return self.logout(request)


class MeUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        response_serializer = UserSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UserAvatar(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UserAvatarSerializer(request.user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.avatar.delete()
        instance = serializer.save()
        # todo response no content
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response["Location"] = build_absolute_uri(instance.avatar.url)
        return response


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def user_info(request, username):
    try:
        user = UserModel.objects.get(username=username)
    except UserModel.DoesNotExist:
        raise Http404
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
