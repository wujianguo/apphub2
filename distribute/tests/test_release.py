import os, requests, shutil
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserReleaseTest(BaseTestCase):

    def setUp(self):
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
        self.apk_path = 'downloads/android-sample.apk'
        if not os.path.exists(self.apk_path):
            url = 'https://raw.githubusercontent.com/bitbar/test-samples/master/apps/android/bitbar-sample-app.apk'
            with requests.get(url, stream=True) as r:
                with open(self.apk_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        self.ipa_path = 'downloads/ios-sample.ipa'
        if not os.path.exists(self.ipa_path):
            url = 'https://raw.githubusercontent.com/bitbar/test-samples/master/apps/ios/bitbar-ios-sample.ipa'
            with requests.get(url, stream=True) as r:
                with open(self.ipa_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def kind(self):
        return 'User'

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def release_app(self, app):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        namespace.create_app(app)
        path = app['path']

        app_api = namespace.get_app_api(path)
        r = app_api.upload_package(self.apk_path)
        package_id = r.json()['package_id']

        release = {
            'package_id': package_id,
            'enabled': True
        }
        r = app_api.create_release(release)
        self.app_api = app_api
        return r.json()

    def test_create_success(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        app["enable_os"] = ["iOS"]
        namespace.create_app(app)
        path = app['path']

        app_api = namespace.get_app_api(path)
        r = app_api.upload_package(self.ipa_path)
        self.assert_status_201(r)
        package_id = r.json()['package_id']

        release = {
            'package_id': package_id,
            'enabled': True
        }
        r = app_api.create_release(release)
        self.assert_status_201(r)
        release_id = r.json()['release_id']
        r2 = app_api.get_release_list()
        self.assert_status_200(r2)
        self.assert_list_length(r2, 1)
        self.assertDictEqual(r.json(), r2.json()[0])
        r = app_api.get_one_release(release_id)
        self.assert_status_200(r)
        self.assertDictEqual(r.json(), r2.json()[0])

    def test_vivo_store(self):
        app = self.chrome_app()
        r = self.release_app(app)
        release_id = r['release_id']
        auth_data = {
            'access_key': 'test_access_key',
            'access_secret': 'test_access_secret',
            'vivo_store_app_id': 'test_vivo_store_app_id',
            'store_app_link': 'https://apphub.libms.top/mock/store/vivo'
        }
        r = self.app_api.create_vivo_store(auth_data)
        self.assert_status_201(r)
        r2 = self.app_api.get_vivo_store()
        self.assert_status_200(r2)
        self.assertDictEqual(r.json(), r2.json())
        # r = self.app_api.submit_store(release_id, '', 'Vivo')
        # self.assert_status_201(r)

class OrganizationReleaseTest(UserReleaseTest):

    def kind(self):
        return 'Organization'

    def suffix_namespace(self, namespace):
        return namespace + '_org'

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        org = self.generate_org(1, visibility=visibility)
        org['path'] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

    def get_namespace(self, api, namespace):
        api.get_org_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_org_api(namespace).get_app_api(app_path)

