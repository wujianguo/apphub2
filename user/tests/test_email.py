from django.core import mail

from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserEmailTest(BaseTestCase):
    def register(self, email=None):
        user = {
            "username": "BillGates",
            "first_name": "Bill",
            "last_name": "Gates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        if email:
            user["email"] = email
        api: Api = Api(UnitTestClient())
        api.get_user_api().register(user)
        return api

    def test_invalid_code(self):
        user = {
            "username": "BillGates",
            "first_name": "Bill",
            "last_name": "Gates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
            "email": self.get_random_email(),
        }
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_201(r)

        r = api.get_user_api().verify_register_email("code")
        self.assert_status_404(r)
        r = api.get_user_api().verify_register_email(
            "5e641c87-bc57-4c77-a6cd-69d685a5ba8f"
        )
        self.assert_status_404(r)

    def test_send_multi_email(self):
        user = {
            "username": "BillGates",
            "first_name": "Bill",
            "last_name": "Gates",
            "password1": "BillGates@password",
            "password2": "BillGates@password",
            "email": self.get_random_email(),
        }
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_201(r)
        r = api.get_user_api().resend_register_email(user["email"])
        self.assert_status_200(r)
        r = api.get_user_api().resend_register_email(user["email"])
        self.assert_status_200(r)

        code = self.get_email_verify_code(mail.outbox[-2].body)
        r = api.get_user_api().verify_register_email(code)
        self.assert_status_200(r)

    # def test_expired(self):
    #     user = {
    #         'username': 'BillGates',
    #         'first_name': 'Bill',
    #         'last_name': 'Gates',
    #         'password1': 'BillGates@password',
    #         'password2': 'BillGates@password',
    #         'email': 'BillGates@example.com'
    #     }
    #     api: Api = Api(UnitTestClient())
    #     r = api.get_user_api().register(user)
    #     self.assert_status_201(r)

    #     time.sleep(5)
    #     code = self.get_email_verify_code(mail.outbox[-1].body)
    #     r = api.get_user_api().verify_register_email(code)
    #     self.assert_status_404(r)
