from client.api import Api
from client.unit_test_client import UnitTestClient
from distribute.tests.test_distribute_base import DistributeBaseTest


class UserUploadPackageTest(DistributeBaseTest):

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def assert_upload(self, file_path):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        app["enable_os"] = ["iOS", "Android"]
        namespace.create_app(app)
        path = app['path']

        app_api = namespace.get_app_api(path)
        r = app_api.upload_package(file_path)
        self.assert_status_201(r)
        package_id = r.json()['package_id']

        r2 = app_api.get_package_list()
        self.assert_status_200(r2)
        self.assert_list_length(r2, 1)
        self.assertDictEqual(r.json(), r2.json()[0])
        r = app_api.get_one_package(package_id)
        self.assert_status_200(r)
        self.assertDictEqual(r.json(), r2.json()[0])

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_namespace(anonymous, larry.client.username).get_app_api(path)
        r = anonymous_app_api.update_app(file_path)
        self.assert_status_401(r)

        app_api = namespace.get_app_api(app['path'])
        token_obj = {
            'name': 'token1',
            'enable_upload_package': True,
        }
        r = app_api.create_token(token_obj)
        self.assert_status_201(r)
        token = r.json()['token']
        r = anonymous_app_api.upload_package(file_path, token)
        self.assert_status_201(r)


    def test_ipa_upload(self):
        self.assert_upload(self.ipa_path)

    def test_apk_upload(self):
        self.assert_upload(self.apk_path)


class OrganizationUploadPackageTest(UserUploadPackageTest):

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        org = self.generate_org(1, visibility=visibility)
        org['path'] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

    def get_namespace(self, api, namespace):
        return api.get_org_api(namespace)
