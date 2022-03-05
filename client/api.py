from client.client import BaseClient


class Api:

    class UserApi():
        def __init__(self, client: BaseClient, username=''):
            self.username = username
            if not self.username:
                self.username = client.username
            self.client = client

        def set_username(self, username):
            self.username = username

        def force_login_or_register(self, username):
            password = username + '@password'
            user = {
                'username': username,
                'password': password
            }
            r = self.login(user)
            if r.status_code != 200:
                self.register(user)

        def register(self, user):
            r = self.client.post('/user/register', user)
            if r.status_code == 201:
                self.username = r.json()['username']
                self.client.set_username(self.username)
                self.client.set_token(r.json()['token'])
            return r

        def login(self, user):
            r = self.client.post('/user/login', user)
            if r.status_code == 200:
                self.username = r.json()['username']
                self.client.set_username(self.username)
                self.client.set_token(r.json()['token'])
            return r

        def logout(self):
            return self.client.post('/user/logout')

        def me(self):
            return self.client.get('/user')

    def __init__(self, client, username='', auto_login=False):
        self.client = client
        if username and auto_login:
            self.get_user_api().force_login_or_register(username)

    def get_user_api(self, username=''):
        return Api.UserApi(self.client, username)
