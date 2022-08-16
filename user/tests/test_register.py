# from django.conf import settings
from django.core import mail

from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserRegisterTest(BaseTestCase):
    def assert_register_success(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_201(r)
        code = self.get_email_verify_code(mail.outbox[-1].body)
        r = api.get_user_api().confirm_register(code)
        self.assert_status_200(r)
        login_req = {"username": user["username"], "password": user["password1"]}
        r = api.get_user_api().login(login_req)
        self.assert_status_200(r)

        assert_keys = ["username", "email", "first_name", "last_name"]
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)
        r = api.get_user_api().me()
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)

        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().login(
            {"username": user["username"], "password": user["password1"]}
        )
        self.assert_status_200(r)
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_user(user["username"])
        self.assert_status_200(r)
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)
        avatar_url = r.json()["avatar"]
        r = anonymous.get_or_head_file(avatar_url)
        self.assert_status_200(r)

    def assert_register_failure_400(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_400(r)

    def assert_register_failure_409(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_409(r)

    def test_register_success(self):
        users = [
            {
                "username": "BillGates",
                "first_name": "Bill",
                "last_name": "Gates",
                "email": self.get_random_email(),
                "password1": "BillGates@password",
                "password2": "BillGates@password",
            },
            {
                "username": "BillGates2",
                "email": self.get_random_email(),
                "password1": "BillGates@password",
                "password2": "BillGates@password",
                # }, {
                #     'username': 'BillGates3',
                #     'password1': 'BillGates3@password',
                #     'password2': 'BillGates3@password',
            },
        ]

        for user in users:
            self.assert_register_success(user)

    def test_username_required(self):
        user = {
            "email": self.get_random_email(),
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        self.assert_register_failure_400(user)

    def test_password_required(self):
        user = {
            "username": "BillGates",
            "email": self.get_random_email(),
        }
        self.assert_register_failure_400(user)

    def test_invalid_username(self):
        users = [
            {
                "username": "",
                "email": self.get_random_email(),
                "password1": "BillGates@password",
                "password2": "BillGates@password",
            },
            {
                "username": "BillGates*",
                "email": self.get_random_email(),
                "password1": "BillGates@password",
                "password2": "BillGates@password",
            },
            {
                "username": "BillGates@example",
                "email": self.get_random_email(),
                "password1": "BillGates@password",
                "password2": "BillGates@password",
            },
        ]
        for user in users:
            self.assert_register_failure_400(user)

    def test_reserved_username(self):
        user = {
            "username": "about",
            "email": self.get_random_email(),
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        self.assert_register_failure_400(user)

    def test_duplicate_username(self):
        user = {
            "username": "BillGates2",
            "email": self.get_random_email(),
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        self.assert_register_success(user)
        self.assert_register_failure_400(user)

    def test_invalid_email(self):
        user = {
            "email": "BillGates@",
            "username": "BillGates2",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        self.assert_register_failure_400(user)

    def test_invalid_password(self):
        user = {
            "username": "BillGates2",
            "email": self.get_random_email(),
        }
        passwords = [
            "",
        ]
        for password in passwords:
            user["password1"] = password
            user["password2"] = password
            self.assert_register_failure_400(user)
