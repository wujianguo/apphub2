from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserRegisterTest(BaseTestCase):

    def assert_register_success(self, user):
        api: Api = Api(UnitTestClient())
        r = api.get_user_api().register(user)
        self.assert_status_201(r)
        assert_keys = ['username', 'email', 'first_name', 'last_name']
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)
        r = api.get_user_api().me()
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)

        api2: Api = Api(UnitTestClient())
        r = api2.get_user_api().login({'account': user['username'], 'password': user['password']})
        self.assert_status_200(r)
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_user(user['username'])
        self.assert_status_200(r)
        self.assert_partial_dict_equal2(user, r.json(), assert_keys)

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
                'username': 'BillGates',
                'first_name': 'Bill',
                'last_name': 'Gates',
                'email': 'BillGates@example.com',
                'password': 'BillGates@password'
            },
            {
                'username': 'BillGates2',
                'email': 'BillGates2@example.com',
                'password': 'BillGates@password'
            }, {
                'username': 'BillGates3',
                'password': 'BillGates3@password'
            }
        ]

        for user in users:
            self.assert_register_success(user)

    def test_username_required(self):
        user = {
            'password': 'BillGates@password'
        }
        self.assert_register_failure_400(user)

    def test_password_required(self):
        user = {
            'username': 'BillGates',
        }
        self.assert_register_failure_400(user)

    def test_invalid_username(self):
        users = [
            {
                'username': '',
                'password': 'BillGates@password'
            }, {
                'username': 'BillGates*',
                'password': 'BillGates@password'
            }, {
                'username': 'BillGates@example',
                'password': 'BillGates@password'
            }
        ]
        for user in users:
            self.assert_register_failure_400(user)

    def test_reserved_username(self):
        user = {
            'username': 'about',
            'password': 'BillGates@password'
        }
        self.assert_register_failure_409(user)

    def test_duplicate_username(self):
        user = {
            'username': 'BillGates',
            'password': 'BillGates@password'
        }
        self.assert_register_success(user)
        self.assert_register_failure_400(user)

    def test_invalid_email(self):
        user = {
            'username': 'BillGates',
            'email': 'BillGates@',
            'password': 'BillGates@password'
        }
        self.assert_register_failure_400(user)

    # def test_duplicate_email(self):
    #     user = {
    #         'username': 'BillGates',
    #         'email': 'BillGates@example.com',
    #         'password': 'BillGates@password'
    #     }
    #     self.assert_register_success(user)
    #     user['username'] += '1'
    #     self.assert_register_failure_400(user)

    def test_invalid_password(self):
        user = {
            'username': 'BillGates',
        }
        passwords = [
            '',
        ]
        for password in passwords:
            user['password'] = password
            self.assert_register_failure_400(user)
