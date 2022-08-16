from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserUpdateTest(BaseTestCase):
    def register(self):
        user = {
            "username": "BillGates",
            "first_name": "Bill",
            "last_name": "Gates",
            "email": self.get_random_email(),
            # 'email': 'bill@example.com',
            "password1": "BillGates@password",
            "password2": "BillGates@password",
        }
        api: Api = Api(UnitTestClient())
        self.login_or_create(api, user)
        return api

    def test_update_username(self):
        api = self.register()
        r = api.get_user_api().update({"username": "*&ya"})
        self.assert_status_400(r)
        new_username = "new_username"
        user = {"username": new_username}
        r = api.get_user_api().update(user)
        self.assert_status_200(r)
        self.assertEqual(r.json()["username"], new_username)
        api.get_user_api().set_username(new_username)
        r = api.get_user_api().me()
        self.assertEqual(r.json()["username"], new_username)

    def test_update_name(self):
        api = self.register()
        user = {"first_name": "Bill2"}
        r = api.get_user_api().update(user)
        self.assertEqual(r.json()["first_name"], "Bill2")
        self.assert_status_200(r)
        r = api.get_user_api().me()
        self.assertEqual(r.json()["first_name"], "Bill2")

    # def test_update_email(self):
    #     api = self.register()
    #     new_email = 'BillGates2@example.com'
    #     user = {
    #         'email': new_email
    #     }
    #     r = api.get_user_api().update(user)
    #     self.assertEqual(r.json()['email'], new_email)
    #     self.assertEqual(r.json()['email_verified'], False)
    #     self.assert_status_200(r)
    #     r = api.get_user_api().me()
    #     self.assertEqual(r.json()['email'], new_email)
    #     self.assertEqual(r.json()['email_verified'], False)

    def test_update_avatar(self):
        api = self.register()
        r = api.get_user_api().update_avatar()
        self.assert_status_204(r)
