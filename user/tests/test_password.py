import time
from django.core import mail
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserPasswordTest(BaseTestCase):

    def register(self, password=None, email=None):
        user = {
            'username': 'BillGates',
            'first_name': 'Bill',
            'last_name': 'Gates',
            'password': 'BillGates@password'
        }
        if password:
            user['password'] = password
        if email:
            user['email'] = email
        api: Api = Api(UnitTestClient())
        api.get_user_api().register(user)
        return api

    def test_change_password_success(self):
        old_password = 'old_password'
        new_password = 'new_password'
        api = self.register(password=old_password)
        r = api.get_user_api().change_password(old_password, new_password)
        self.assert_status_204(r)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().login({'account': 'BillGates', 'password': new_password})
        self.assert_status_200(r)

    def test_change_password_failure(self):
        old_password = 'old_password'
        new_password = 'new_password'
        api = self.register(password=old_password)
        r = api.get_user_api().change_password('hello', new_password)
        self.assert_status_400(r)
        r = api.get_user_api().change_password(old_password, '')
        self.assert_status_400(r)

    def test_reset_password_success(self):
        email = 'BillGates@example.com'
        api = self.register(email=email)
        r = api.get_user_api().request_verify_email()
        self.assert_status_204(r)
        code = str(mail.outbox[0].body)
        r = api.get_user_api().verify_email(code)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_204(r)
        code = str(mail.outbox[1].body)
        new_password = 'new_password'
        r = api2.get_user_api().reset_password(code, new_password)
        self.assert_status_204(r)
        api3: Api = Api(UnitTestClient())
        r = api3.get_user_api().login({'account': 'BillGates', 'password': new_password})
        self.assert_status_200(r)

    def test_reset_password_invalid_code(self):
        email = 'BillGates@example.com'
        api = self.register(email=email)
        r = api.get_user_api().request_verify_email()
        self.assert_status_204(r)
        code = str(mail.outbox[0].body)
        r = api.get_user_api().verify_email(code)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_204(r)

        new_password = 'new_password'
        r = api2.get_user_api().reset_password(code, new_password)
        self.assert_status_400(r)
        r = api2.get_user_api().reset_password('code', new_password)
        self.assert_status_400(r)

    def test_reset_password_no_email(self):
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password('BillGates@example.com')
        self.assert_status_400(r)

    def test_reset_password_email_not_verified(self):
        email = 'BillGates@example.com'
        self.register(email=email)

        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_400(r)

    def test_reset_password_expire(self):
        email = 'BillGates@example.com'
        api = self.register(email=email)
        r = api.get_user_api().request_verify_email()
        self.assert_status_204(r)
        code = str(mail.outbox[0].body)
        r = api.get_user_api().verify_email(code)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_204(r)
        code = str(mail.outbox[1].body)
        new_password = 'new_password'
        with self.settings(CODE_EXPIRE_SECONDS=1):
            time.sleep(5)
            r = api2.get_user_api().reset_password(code, new_password)
            self.assert_status_400(r)

    def test_reset_password_send_multi_email(self):
        email = 'BillGates@example.com'
        api = self.register(email=email)
        r = api.get_user_api().request_verify_email()
        self.assert_status_204(r)
        code = str(mail.outbox[0].body)
        r = api.get_user_api().verify_email(code)
        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().request_reset_password(email)
        r = api2.get_user_api().request_reset_password(email)
        r = api2.get_user_api().request_reset_password(email)
        self.assert_status_204(r)
        code = str(mail.outbox[3].body)
        new_password = 'new_password'
        r = api2.get_user_api().reset_password(code, new_password)
        self.assert_status_204(r)
        api3: Api = Api(UnitTestClient())
        r = api3.get_user_api().login({'account': 'BillGates', 'password': new_password})
        self.assert_status_200(r)
