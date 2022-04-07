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

    def create_and_get_user(self, username='LarryPage', auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        return api.get_user_api(namespace)

    def create_and_get_org_namespace(self, api, namespace, visibility='Public'):
        org = self.generate_org(1, visibility=visibility)
        org['path'] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_user_api(namespace).get_app_api(app_path)

    def test_visible_apps(self):
        larry = self.create_and_get_user()
        bill = self.create_and_get_user('BillGates')
        mark = self.create_and_get_user('Mark')
        anonymous: Api = Api(UnitTestClient())

        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app1 = self.generate_app(1, visibility='Public')
        namespace.create_app(app1)
        larry.get_user_api().get_visible_app_list()
        bill.get_user_api().get_visible_app_list()
        mark.get_user_api().get_visible_app_list()
        anonymous.get_user_api().get_visible_app_list()

        app2 = self.generate_app(2, visibility='Internal')
        namespace.create_app(app2)

        app3 = self.generate_app(3, visibility='Private')
        namespace.create_app(app3)

        bill_namespace = self.create_and_get_namespace(bill, larry.client.username)
        app4 = self.generate_app(4, visibility='Public')
        bill_namespace.create_app(app4)

        app5 = self.generate_app(5, visibility='Internal')
        bill_namespace.create_app(app5)

        app6 = self.generate_app(6, visibility='Private')
        bill_namespace.create_app(app6)

        larry_org1 = self.create_and_get_org_namespace(larry, 'larry_org1', visibility='Public')
        app7 = self.generate_app(7, visibility='Public')
        larry_org1.create_app(app7)

        app8 = self.generate_app(8, visibility='Internal')
        larry_org1.create_app(app8)

        app9 = self.generate_app(9, visibility='Private')
        larry_org1.create_app(app9)

        larry_org2 = self.create_and_get_org_namespace(larry, 'larry_org2', visibility='Internal')
        app10 = self.generate_app(10, visibility='Public')
        larry_org2.create_app(app10)

        app11 = self.generate_app(11, visibility='Internal')
        larry_org2.create_app(app11)

        app12 = self.generate_app(12, visibility='Private')
        larry_org2.create_app(app12)

        larry_org3 = self.create_and_get_org_namespace(larry, 'larry_org3', visibility='Private')
        app13 = self.generate_app(13, visibility='Public')
        larry_org3.create_app(app13)

        app14 = self.generate_app(14, visibility='Internal')
        larry_org3.create_app(app14)

        app15 = self.generate_app(15, visibility='Private')
        larry_org3.create_app(app15)


        bill_org1 = self.create_and_get_org_namespace(bill, 'bill_org1', visibility='Public')
        app16 = self.generate_app(16, visibility='Public')
        bill_org1.create_app(app16)

        app17 = self.generate_app(17, visibility='Internal')
        bill_org1.create_app(app17)

        app18 = self.generate_app(18, visibility='Private')
        bill_org1.create_app(app18)

        bill_org2 = self.create_and_get_org_namespace(bill, 'bill_org2', visibility='Internal')
        app19 = self.generate_app(19, visibility='Public')
        bill_org2.create_app(app19)

        app20 = self.generate_app(20, visibility='Internal')
        bill_org2.create_app(app20)

        app21 = self.generate_app(21, visibility='Private')
        bill_org2.create_app(app21)

        bill_org3 = self.create_and_get_org_namespace(bill, 'bill_org3', visibility='Private')
        app22 = self.generate_app(22, visibility='Public')
        bill_org3.create_app(app22)

        app23 = self.generate_app(23, visibility='Internal')
        bill_org3.create_app(app23)

        app24 = self.generate_app(24, visibility='Private')
        bill_org3.create_app(app24)

        larry.get_user_api().get_visible_app_list()
        bill.get_user_api().get_visible_app_list()
        mark.get_user_api().get_visible_app_list()
        anonymous.get_user_api().get_visible_app_list()
