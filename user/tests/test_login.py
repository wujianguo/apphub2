from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserLoginTest(BaseTestCase):
    def assert_login_success(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().login(user)
        self.assert_status_200(r)

    def assert_login_failure(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().login(user)
        self.assert_status_400(r)

    def register(self, user):
        api: Api = Api(UnitTestClient())
        self.login_or_create(api, user)

    def test_login_success(self):
        user = {
            "username": "BillGates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
            "email": self.get_random_email(),
        }
        self.register(user)
        self.assert_login_success(
            {"username": "BillGates", "password": "BillGates@password"}
        )

    def test_login_failure(self):
        user = {
            "username": "BillGates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
            "email": self.get_random_email(),
        }
        self.register(user)
        users = [
            {"username": "BillGates", "password": "BillGates@passwordxx"},
            {"username": "BillGates3", "password": "BillGates@password"},
            {
                "username": "BillGates",
            },
            {"password": "BillGates@password"},
            {"email": self.get_random_email(), "password": "BillGates@passwordxx"},
        ]
        for user in users:
            self.assert_login_failure(user)

    def test_logout(self):
        user = {
            "username": "BillGates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
            "email": self.get_random_email(),
        }
        self.register(user)
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().login(
            {"username": "BillGates", "password": "BillGates@password"}
        )

        r = api.get_user_api().logout()
        self.assert_status_200(r)
        r = api.get_user_api().me()
        self.assert_status_401(r)
