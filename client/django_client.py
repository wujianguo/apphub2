from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

from client.client import BaseClient

UserModel = get_user_model()


class DjangoTestClient(BaseClient):
    def __init__(self, base_url=""):
        self.base_url = base_url
        if settings.API_URL_PREFIX:
            self.base_url += "/" + settings.API_URL_PREFIX
        self.token = ""
        self.username = ""
        self.client = Client()

    def login_or_create(self, username):
        user, created = UserModel.objects.get_or_create(username=username)
        self.client.force_login(user)
        return user

    def set_token(self, token):
        if token is not None:
            self.token = "Bearer " + token
        else:
            self.token = ""

    def set_username(self, username):
        self.username = username

    def build_url(self, path):
        if path.startswith(self.base_url):
            return path
        return self.base_url + path

    def get_or_head_file(self, path, query=None):
        if path.startswith(settings.EXTERNAL_API_URL):
            path = path[len(settings.EXTERNAL_API_URL) :]
        return self.client.head(
            self.build_url(path), data=query, HTTP_AUTHORIZATION=self.token
        )

    def get(self, path, query=None):
        return self.client.get(
            self.build_url(path), data=query, HTTP_AUTHORIZATION=self.token
        )

    def post(self, path, body=None):
        content_type = "application/json"
        return self.client.post(
            self.build_url(path),
            body,
            content_type=content_type,
            HTTP_AUTHORIZATION=self.token,
        )

    def put(self, path, body):
        content_type = "application/json"
        return self.client.put(
            self.build_url(path),
            body,
            content_type=content_type,
            HTTP_AUTHORIZATION=self.token,
        )

    def delete(self, path):
        return self.client.delete(self.build_url(path), HTTP_AUTHORIZATION=self.token)

    def upload_post(self, path, data, token=None):
        if token:
            return self.client.post(
                self.build_url(path),
                data=data,
                format="multipart",
                HTTP_AUTHORIZATION="Token " + token,
            )
        return self.client.post(
            self.build_url(path),
            data=data,
            format="multipart",
            HTTP_AUTHORIZATION=self.token,
        )
