import os, requests, shutil
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

def skip_if_base(func):
    def wrap(self, *args, **kwargs):
        if not self.kind():
            self.skipTest('skip base.')
            return
        return func(self, *args, **kwargs)
    return wrap

class BaseUploadPackageTest(BaseTestCase):

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

    def kind(self):
        return ''

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        pass

    @skip_if_base
    def test_ipa_upload(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        app["enable_os"] = ["iOS"]
        namespace.create_app(app)
        path = app['path']

        app_api = namespace.get_app_api(path)
        r = app_api.upload_package(self.ipa_path)
        self.assert_status_201(r)
        internal_build = r.json()['internal_build']

        r2 = app_api.get_package_list()
        self.assert_status_200(r2)
        self.assert_list_length(r2, 1)
        self.assertDictEqual(r.json(), r2.json()[0])
        r = app_api.get_one_package(internal_build)
        self.assert_status_200(r)
        self.assertDictEqual(r.json(), r2.json()[0])

    @skip_if_base
    def test_apk_upload(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        app["enable_os"] = ["Android"]
        namespace.create_app(app)
        path = app['path']

        app_api = namespace.get_app_api(path)
        r = app_api.upload_package(self.apk_path)
        self.assert_status_201(r)
        internal_build = r.json()['internal_build']

        r2 = app_api.get_package_list()
        self.assert_status_200(r2)
        self.assert_list_length(r2, 1)
        self.assertDictEqual(r.json(), r2.json()[0])
        r = app_api.get_one_package(internal_build)
        self.assert_status_200(r)
        self.assertDictEqual(r.json(), r2.json()[0])

class UserUploadPackageTest(BaseUploadPackageTest):

    def kind(self):
        return 'User'

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)
