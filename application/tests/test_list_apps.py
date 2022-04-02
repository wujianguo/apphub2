from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class UserUniversalAppListTest(BaseTestCase):

    def kind(self):
        return 'User'

    def suffix_namespace(self, namespace):
        return namespace

    def create_and_get_user(self, username='LarryPage', auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_user_api(namespace).get_app_api(app_path)

    def test_empty_orgs(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        r = namespace.get_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)

    def test_less_than_one_page(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        number = 6
        for i in range(number):
            app = self.generate_app(i)
            r = namespace.create_app(app)
            self.assert_status_201(r)
        r = namespace.get_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, number)

    def test_more_than_one_page(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        number = 36
        app_list = []
        for i in range(number):
            app = self.generate_app(i, 'Public')
            app_list.append(app)
            r = namespace.create_app(app)
            self.assert_status_201(r)

        r = namespace.get_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list = self.get_resp_list(r)
        anonymous: Api = Api(UnitTestClient())
        anonymous_namespace = self.get_namespace(anonymous, larry.client.username)
        r = anonymous_namespace.get_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_app_list[i], app_list[i], ['name'])
            self.assert_partial_dict_equal(resp_app_list2[i], app_list[i], ['name'])
            
        r = namespace.get_app_list(page=2, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list = self.get_resp_list(r)
        r = anonymous_namespace.get_app_list(page=2, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_app_list[i], app_list[i+10], ['name'])
            self.assert_partial_dict_equal(resp_app_list2[i], app_list[i+10], ['name'])

        r = namespace.get_app_list(page=3, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list = self.get_resp_list(r)
        r = anonymous_namespace.get_app_list(page=3, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_app_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_app_list[i], app_list[i+20], ['name'])
            self.assert_partial_dict_equal(resp_app_list2[i], app_list[i+20], ['name'])

        r = namespace.get_app_list(page=4, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 6)
        resp_app_list = self.get_resp_list(r)
        r = anonymous_namespace.get_app_list(page=4, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 6)
        resp_app_list2 = self.get_resp_list(r)
        for i in range(6):
            self.assert_partial_dict_equal(resp_app_list[i], app_list[i+30], ['name'])
            self.assert_partial_dict_equal(resp_app_list2[i], app_list[i+30], ['name'])

        r = namespace.get_app_list(page=5, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 0)
        r = anonymous_namespace.get_app_list(page=5, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 0)

        r = namespace.get_app_list(page=-1, per_page=10)
        self.assert_status_400(r)

        r = namespace.get_app_list(page=1, per_page=101)
        self.assert_status_400(r)

        r = namespace.get_app_list(page=1, per_page=-1)
        self.assert_status_400(r)

        r = namespace.get_app_list(page='a', per_page=10)
        self.assert_status_400(r)

        r = namespace.get_app_list(page=1, per_page='a')
        self.assert_status_400(r)

        r = namespace.get_app_list(page=1, per_page=100)
        self.assert_status_200(r)


class OrganizationUniversalAppListTest(UserUniversalAppListTest):

    def kind(self):
        return 'Organization'

    def suffix_namespace(self, namespace):
        return namespace + '_org'

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        org = self.generate_org(1, visibility=visibility)
        org['path'] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

    def get_namespace(self, api, namespace):
        return api.get_org_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_org_api(namespace).get_app_api(app_path)

class UserVisibleAppListTest(BaseTestCase):
    pass
