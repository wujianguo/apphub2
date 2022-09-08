from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserStoreAppAuthTest(BaseTestCase):

    def create_and_get_user(self, username="LarryPage"):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def create_app(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        app["enable_os"] = ["iOS", "Android"]
        namespace.create_app(app)
        return larry, namespace.get_app_api(app["path"]), app["path"]

    def setUp(self):
        super().setUp()
        larry, app_api, path = self.create_app()
        self.app_api = app_api

    def test_appstore(self):
        app_api = self.app_api
        r = app_api.create_appstore("414478124", "cn")
        self.assert_status_201(r)
        r2 = app_api.get_appstore_auth()
        self.assertDictEqual(r.json(), r2.json())

    def test_huawei(self):
        app_api = self.app_api
        store_url = "https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&maxResults=25&uri=app%7CC5683&shareTo=weixin&currentUrl=https%253A%252F%252Fappgallery.huawei.com%252Fapp%252FC5683%253FsharePrepath%253Dag%2526locale%253Dzh_CN%2526source%253Dappshare%2526subsource%253DC5683%2526shareTo%253Dweixin%2526shareFrom%253Dappmarket%2526shareIds%253D35849d40b3c94bfd8f204a1c87fceb10_1%2526callType%253DSHARE&accessId=&appid=C5683&zone=&locale=zh"  # noqa: E501
        store_link = store_url
        r = app_api.create_huawei_store(store_url, store_link)
        self.assert_status_201(r)
        r2 = app_api.get_huawei_auth()
        self.assertDictEqual(r.json(), r2.json())

    def test_vivo(self):
        app_api = self.app_api
        r = app_api.create_vivo_store("40413")
        self.assert_status_201(r)
        r2 = app_api.get_vivo_auth()
        self.assertDictEqual(r.json(), r2.json())

    def test_xiaomi(self):
        app_api = self.app_api
        r = app_api.create_xiaomi_store("1122")
        self.assert_status_201(r)
        r2 = app_api.get_xiaomi_auth()
        self.assertDictEqual(r.json(), r2.json())

    def test_yingyongbao(self):
        app_api = self.app_api
        r = app_api.create_yingyongbao_store("com.tencent.mm")
        self.assert_status_201(r)
        r2 = app_api.get_yingyongbao_auth()
        self.assertDictEqual(r.json(), r2.json())

    def test_duplicate(self):
        app_api = self.app_api
        r = app_api.create_yingyongbao_store("com.tencent.mm")
        self.assert_status_201(r)
        r2 = app_api.get_yingyongbao_auth()
        self.assertDictEqual(r.json(), r2.json())
        r = app_api.create_yingyongbao_store("com.tencent.mm")
        self.assert_status_409(r)

    def test_stores(self):
        self.test_appstore()
        self.test_huawei()
        self.test_vivo()
        self.test_xiaomi()
        self.test_yingyongbao()
        r = self.app_api.get_stores()
        self.assert_status_200(r)
        self.assert_list_length(r, 5)
        r = self.app_api.update_stores_versions()
        self.assert_status_200(r)
        r = self.app_api.get_stores_versions()
        self.assert_status_200(r)


class OrganizationStoreAppAuthTest(UserStoreAppAuthTest):

    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        org = self.generate_org(1, visibility=visibility)
        org["path"] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org["path"])


class StoreAppVersionTest(BaseTestCase):
    def assert_valid_version(self, r):
        version = r.json()["version"]
        self.assertEqual(len(version.split(".")), 3, version)

    def test_appstore(self):
        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_appstore_app_version("414478124", "cn")
        self.assert_valid_version(r)

    def test_huawei(self):
        anonymous: Api = Api(UnitTestClient())
        store_url = "https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&maxResults=25&uri=app%7CC5683&shareTo=weixin&currentUrl=https%253A%252F%252Fappgallery.huawei.com%252Fapp%252FC5683%253FsharePrepath%253Dag%2526locale%253Dzh_CN%2526source%253Dappshare%2526subsource%253DC5683%2526shareTo%253Dweixin%2526shareFrom%253Dappmarket%2526shareIds%253D35849d40b3c94bfd8f204a1c87fceb10_1%2526callType%253DSHARE&accessId=&appid=C5683&zone=&locale=zh"  # noqa: E501
        r = anonymous.get_huawei_app_version(store_url)
        self.assert_valid_version(r)

    def test_vivo(self):
        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_vivo_app_version("40413")
        self.assert_valid_version(r)

    def test_xiaomi(self):
        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_xiaomi_app_version("1122")
        self.assert_valid_version(r)

    def test_yingyongbao(self):
        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_yingyongbao_app_version("com.tencent.mm")
        self.assert_valid_version(r)
