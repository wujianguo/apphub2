from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


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
