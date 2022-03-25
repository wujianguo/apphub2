from client.client import BaseClient
from util.image import generate_random_image


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

        def update(self, user):
            return self.client.put('/user', user)

        def update_avatar(self, avatar_file_path=None):
            if avatar_file_path is None:
                file = generate_random_image()
                file_path = file.name
            else:
                file_path = avatar_file_path

            with open(file_path, 'rb') as fp:
                data = {'avatar': fp}
                return self.client.upload_post('/user/avatar', data=data)

        def change_password(self, password, new_password):
            payload = {
                'password': password,
                'new_password': new_password
            }
            return self.client.post('/user/password/change', payload)

        def request_reset_password(self, email):
            payload = {
                'email': email
            }
            return self.client.post('/user/password/request_reset', payload)

        def reset_password(self, code, password):
            payload = {
                'code': code,
                'password': password
            }
            return self.client.post('/user/password/reset', payload)

        def request_verify_email(self):
            return self.client.post('/user/email/request_verify')

        def verify_email(self, code):
            payload = {
                'code': code
            }
            return self.client.post('/user/email/verify', payload)

        def create_org(self, org):
            return self.client.post('/orgs', org)

        def get_org_list(self, page=1, per_page=10):
            query = {
                'page': page,
                'per_page': per_page
            }
            return self.client.get('/orgs', query)

        def get_app_api(self, path):
            return Api.UniversalAppApi(self.client, path, self.username)

        def create_app(self, app):
            return self.client.post('/apps', app)

        def get_app_list(self, page=1, per_page=10):
            query = {
                'page': page,
                'per_page': per_page
            }
            return self.client.get('/apps', query)

    class OrganizationApi():
        def __init__(self, client, path):
            self.client = client
            self.base_path = '/orgs/' + path
            self.path = path
        
        def get_org(self):
            return self.client.get(self.base_path)

        def update_org(self, org):
            return self.client.put(self.base_path, org)

        def remove_org(self):
            return self.client.delete(self.base_path)

        def change_or_set_icon(self, icon_file_path=None):
            if icon_file_path is None:
                file = generate_random_image()
                file_path = file.name
            else:
                file_path = icon_file_path

            with open(file_path, 'rb') as fp:
                data = {'icon_file': fp}
                return self.client.upload_post(self.base_path + '/icon', data=data)

        def get_icon(self):
            return self.client.get(self.base_path + '/icon')

        def remove_icon(self):
            return self.client.delete(self.base_path + '/icon')

        def add_member(self, username, role):
            collaborator = {
                'username': username,
                'role': role
            }
            return self.client.post(self.base_path + '/members', collaborator)

        def get_member(self, username):
            return self.client.get(self.base_path + '/members/' + username)

        def get_member_list(self):
            return self.client.get(self.base_path + '/members')

        def change_member_role(self, username, role):
            data = {
                'role': role
            }
            return self.client.put(self.base_path + '/members/' + username, data)

        def remove_member(self, username):
            return self.client.delete(self.base_path + '/members/' + username)

        def create_app(self, app):
            return self.client.post(self.base_path + '/apps', app)

        def get_app_list(self, page=1, per_page=10):
            query = {
                'page': page,
                'per_page': per_page
            }
            return self.client.get(self.base_path + '/apps', query)

        def get_app_api(self, path):
            return Api.UniversalAppApi(self.client, path, org=self.path)

    class UniversalAppApi():
        def __init__(self, client, path, owner='', org=''):
            self.client = client
            if owner:
                self.base_path = '/users/' + owner + '/apps/' + path
            if org:
                self.base_path = '/orgs/' + org + '/apps/' + path
        
        def get_app(self):
            return self.client.get(self.base_path)

        def update_app(self, app):
            return self.client.put(self.base_path, app)

        def upload_package(self, file_path):
            with open(file_path, 'rb') as fp:
                data = {'file': fp}
                url = self.base_path + '/packages'
                return self.client.upload_post(url, data=data)

        def get_package_list(self, page=1, per_page=10):
            query = {
                'page': page,
                'per_page': per_page
            }
            return self.client.get(self.base_path + '/packages', query)

        def get_one_package(self, internal_build):
            return self.client.get(self.base_path + '/packages/' + str(internal_build))

        def create_release(self, environment, release):
            return self.client.post(self.base_path + '/releases/' + environment, release)

        def get_release_list(self, environment):
            return self.client.get(self.base_path + '/releases/' + environment)

        def get_one_release(self, release_id):
            return self.client.get(self.base_path + '/releases/' + str(release_id))

        def create_vivo_store(self, auth_data):
            return self.client.post(self.base_path + '/stores/vivo', auth_data)

        def get_vivo_store(self):
            return self.client.get(self.base_path + '/stores/vivo')

        def submit_store(self, release_id, release_notes, store):
            payload = {
                'release_id': release_id,
                'release_notes': release_notes,
                'store': store
            }
            return self.client.post(self.base_path + '/stores/submit', payload)


    def __init__(self, client, username='', auto_login=False):
        self.client = client
        if username and auto_login:
            self.get_user_api().force_login_or_register(username)

    def get_user_api(self, username=''):
        return Api.UserApi(self.client, username)

    def get_org_api(self, path):
        return Api.OrganizationApi(self.client, path)
