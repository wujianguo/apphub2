import requests
from client.client import BaseClient


class RequestsClient(BaseClient):
    def __init__(self, base_url='https://appcenter.libms.top/debug/api/'):
        self.base_url = base_url
        self.token = ''
        self.username = ''

    def set_token(self, token):
        self.token = token

    def set_username(self, username):
        self.username = username

    def build_url(self, path):
        return self.base_url + path

    def headers(self):
        if self.token:
            return {
                'Authorization': 'Bearer ' + self.token
            }
        return {}

    def get_or_head_file(self, path, query=None):
        return requests.head(self.build_url(path), headers=self.headers())

    def get(self, path, query=None):
        return requests.get(self.build_url(path), headers=self.headers())

    def post(self, path, body=None):
        return requests.post(self.build_url(path), json=body, headers=self.headers())

    def put(self, path, body):
        return requests.put(self.build_url(path), json=body, headers=self.headers())

    def delete(self, path):
        return requests.delete(self.build_url(path), headers=self.headers())

    def upload_post(self, path, data, token=None):
        if token:
            headers = {
                'Authorization': 'Token ' + token
            }
            return requests.post(self.build_url(path), files=data, headers=headers)
        return requests.post(self.build_url(path), files=data, headers=self.headers())
