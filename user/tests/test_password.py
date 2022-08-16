from django.core import mail

from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserPasswordTest(BaseTestCase):
    def register(self, password=None, email=None):
        user = {
            "username": "BillGates",
            "first_name": "Bill",
            "last_name": "Gates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        if password:
            user["password1"] = password
            user["password2"] = password
        if email:
            user["email"] = email
        api: Api = Api(UnitTestClient())
        self.login_or_create(api, user)
        return api

    def get_password_reset_confirm_code(self, s):
        key1 = "users/"
        key2 = "/password/reset/confirm/"
        username = s[s.find(key1) + len(key1) : s.find(key2)]
        token = s[s.find(key2) + len(key2) : s.find(key2) + len(key2) + 39]
        return username, token

    def test_change_password_success(self):
        email = self.get_random_email()
        old_password = "old_password"
        new_password = "new_password"
        api = self.register(password=old_password, email=email)
        r = api.get_user_api().change_password(old_password, new_password)
        self.assert_status_200(r)
        r = api.get_user_api().me()
        self.assert_status_401(r)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().login(
            {"username": "BillGates", "password": new_password}
        )
        self.assert_status_200(r)

    def test_change_password_failure(self):
        email = self.get_random_email()
        old_password = "old_password"
        new_password = "new_password"
        api = self.register(password=old_password, email=email)
        r = api.get_user_api().change_password("hello", new_password)
        self.assert_status_400(r)
        r = api.get_user_api().change_password(old_password, "")
        self.assert_status_400(r)

    def test_reset_password_success(self):
        email = self.get_random_email()
        self.register(email=email)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_200(r)
        body = str(mail.outbox[-1].body)
        username, token = self.get_password_reset_confirm_code(body)
        new_password = "new_password"
        r = api2.get_user_api().reset_password(username, token, new_password)
        self.assert_status_200(r)
        api3: Api = Api(UnitTestClient())
        r = api3.get_user_api().login(
            {"username": "BillGates", "password": new_password}
        )
        self.assert_status_200(r)

    def test_reset_password_invalid_code(self):
        email = self.get_random_email()
        self.register(email=email)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_200(r)
        body = str(mail.outbox[-1].body)
        username, token = self.get_password_reset_confirm_code(body)
        new_password = "new_password"
        r = api2.get_user_api().reset_password(username, "token", new_password)
        self.assert_status_400(r)
        r = api2.get_user_api().reset_password("code", token, new_password)
        self.assert_status_400(r)

    def test_reset_password_no_email(self):
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(self.get_random_email())
        self.assert_status_200(r)
        self.assertEqual(len(mail.outbox), 0)

    # def test_reset_password_expire(self):
    #     email = 'BillGates@example.com'
    #     api = self.register(email=email)
    #     r = api.get_user_api().request_verify_email()
    #     self.assert_status_204(r)
    #     code = str(mail.outbox[0].body)
    #     r = api.get_user_api().verify_email(code)
    #     api2: Api = Api(UnitTestClient())
    #     r = api2.get_user_api().request_reset_password(email)
    #     self.assert_status_204(r)
    #     code = str(mail.outbox[1].body)
    #     new_password = 'new_password'
    #     with self.settings(CODE_EXPIRE_SECONDS=1):
    #         time.sleep(5)
    #         r = api2.get_user_api().reset_password(code, new_password)
    #         self.assert_status_400(r)

    def test_reset_password_send_multi_email(self):
        email = self.get_random_email()
        self.register(email=email)

        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_200(r)
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_200(r)
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_200(r)
        body = str(mail.outbox[-1].body)
        username, token = self.get_password_reset_confirm_code(body)
        new_password = "new_password"
        r = api2.get_user_api().reset_password(username, token, new_password)
        self.assert_status_200(r)
        api3: Api = Api(UnitTestClient())
        r = api3.get_user_api().login(
            {"username": "BillGates", "password": new_password}
        )
        self.assert_status_200(r)
