from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class UserAppTokenTest(BaseTestCase):

    def create_and_get_user(self, username='LarryPage', auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def test_create(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        namespace.create_app(app)

        app_api = namespace.get_app_api(app['path'])
        token = {
            'name': 'token1',
            'enable_upload_package': True,
            'enable_get_packages': True,
            'enable_get_releases': True,
            'enable_get_upgrades': True
        }
        r = app_api.create_token({'namm': 'token2'})
        self.assert_status_400(r)

        r = app_api.create_token(token)
        self.assert_status_201(r)
        token_id = r.json()['id']

        r = app_api.get_token_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        r = app_api.get_one_token(token_id)
        self.assert_status_200(r)

        update_token = {
            'enable_get_releases': False
        }
        r = app_api.update_token(token_id, update_token)
        self.assert_status_200(r)

        r = app_api.update_token(token_id, {'enable_get_releases': 'abc'})
        self.assert_status_400(r)

        r = app_api.get_one_token(token_id)
        self.assert_status_200(r)
        self.assertEqual(r.json()['enable_get_releases'], update_token['enable_get_releases'])

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_namespace(anonymous, larry.client.username).get_app_api(app['path'])
        r = anonymous_app_api.get_token_list()
        self.assert_status_401(r)
        r = anonymous_app_api.get_one_token(token_id)
        self.assert_status_401(r)

        r = app_api.remove_token(token_id)
        self.assert_status_204(r)

        r = app_api.get_one_token(token_id)
        self.assert_status_404(r)


class OrganizationAppTokenTest(UserAppTokenTest):

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        org = self.generate_org(1, visibility=visibility)
        org['path'] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

    def get_namespace(self, api, namespace):
        return api.get_org_api(namespace)
