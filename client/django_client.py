from django.test import Client
from client.client import BaseClient


class DjangoTestClient(BaseClient):
    def __init__(self, base_url=''):
        self.base_url = base_url# + '/api'
        self.token = ''
        self.username = ''
        self.client = Client()

    def set_token(self, token):
        if token is not None:
            self.token = 'Bearer ' + token
        else:
            self.token = ''

    def set_username(self, username):
        self.username = username

    def build_url(self, path):
        if path.startswith(self.base_url):
            return path
        return self.base_url + path

    def get_or_head_file(self, path, query=None):
        return self.client.head(self.build_url(path), data=query, HTTP_AUTHORIZATION=self.token)

    def get(self, path, query=None):
        return self.client.get(self.build_url(path), data=query, HTTP_AUTHORIZATION=self.token)

    def post(self, path, body=None):
        content_type = 'application/json'
        return self.client.post(self.build_url(path), body, content_type=content_type, HTTP_AUTHORIZATION=self.token)

    def put(self, path, body):
        content_type = 'application/json'
        return self.client.put(self.build_url(path), body, content_type=content_type, HTTP_AUTHORIZATION=self.token)

    def delete(self, path):
        return self.client.delete(self.build_url(path), HTTP_AUTHORIZATION=self.token)

    def upload_post(self, path, data, token=None):
        if token:
            return self.client.post(self.build_url(path), data=data, format="multipart", HTTP_AUTHORIZATION='Token ' + token)
        return self.client.post(self.build_url(path), data=data, format="multipart", HTTP_AUTHORIZATION=self.token)
