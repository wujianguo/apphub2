import time
from django.core import mail
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserEmailTest(BaseTestCase):

    def register(self, email=None):
        user = {
            'username': 'BillGates',
            'first_name': 'Bill',
            'last_name': 'Gates',
            'password': 'BillGates@password'
        }
        if email:
            user['email'] = email
        api: Api = Api(UnitTestClient())
        api.get_user_api().register(user)
        return api

    def test_verify_email_success(self):
        user = {
            'username': 'BillGates',
            'first_name': 'Bill',
            'last_name': 'Gates',
            'email': 'BillGates@example.com',
            'password': 'BillGates@password'
        }
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assertEqual(r.json()['email_verified'], False)
        r = api.get_user_api().request_verify_email()
        self.assert_status_204(r)
        code = str(mail.outbox[0].body)
        r = api.get_user_api().verify_email(code)
        self.assert_status_204(r)
        r = api.get_user_api().me()
        self.assertEqual(r.json()['email_verified'], True)

        api2: Api = Api(UnitTestClient())
        user['username'] += 'xyz'
        r = api2.get_user_api().register(user)
        self.assert_status_409(r)

    def test_user_do_not_has_an_email(self):
        api = self.register()
        r = api.get_user_api().request_verify_email()
        self.assert_status_400(r)

    def test_invalid_code(self):
        api = self.register('BillGates@example.com')
        r = api.get_user_api().request_verify_email()
        r = api.get_user_api().verify_email('code')
        self.assert_status_400(r)
        r = api.get_user_api().verify_email('5e641c87-bc57-4c77-a6cd-69d685a5ba8f')
        self.assert_status_400(r)

    def test_send_multi_email(self):
        api = self.register('BillGates@example.com')
        r = api.get_user_api().request_verify_email()
        r = api.get_user_api().request_verify_email()
        r = api.get_user_api().request_verify_email()
        code = str(mail.outbox[2].body)
        r = api.get_user_api().verify_email(code)
        self.assert_status_204(r)

    def test_expired(self):
        api = self.register('BillGates@example.com')
        with self.settings(CODE_EXPIRE_SECONDS=1):
            r = api.get_user_api().request_verify_email()
            self.assert_status_204(r)
            code = str(mail.outbox[0].body)
            time.sleep(5)
            r = api.get_user_api().verify_email(code)
            self.assert_status_400(r)
