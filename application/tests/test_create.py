from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserUniversalAppCreateTest(BaseTestCase):

    def create_and_get_user(self, username='LarryPage', auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def kind(self):
        return 'User'

    def suffix_namespace(self, namespace):
        return namespace

    def create_and_get_namespace(self, api, namespace, visibility='Public'):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_user_api(namespace).get_app_api(app_path)

    def test_create_success(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)        
        self.assert_partial_dict_equal(app, r.json(), ['path', 'name', 'visibility', 'description'])
        path = app['path']

        r2 = namespace.get_app_api(path).get_app()
        self.assert_status_200(r2)
        self.assertDictEqual(r.json(), r2.json())

    def test_invalid_path(self):
        # 1. only letters, numbers, underscores or hyphens
        # 2. 0 < len(path) <= 32
        # 3. reserved

        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        app['path'] += '*'
        r = namespace.create_app(app)
        self.assert_status_400(r)

        max_length = 32
        app['path'] = 'a' * max_length
        r = namespace.create_app(app)
        self.assert_status_201(r)

        app['path'] = 'a' * max_length + 'a'
        r = namespace.create_app(app)
        self.assert_status_400(r)

        app['path'] = ''
        r = namespace.create_app(app)
        self.assert_status_400(r)

        del app['path']
        r = namespace.create_app(app)
        self.assert_status_400(r)

        app['path'] = 'about'
        r = namespace.create_app(app)
        self.assert_status_409(r)

    def test_duplicate_path(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        namespace.create_app(app)

        app2 = self.todo_app()
        app2['path'] = app['path']
        r =  namespace.create_app(app2)
        self.assert_status_409(r)

        bill: Api = self.create_and_get_user('BillGates')
        bill_namespace = self.create_and_get_namespace(bill, bill.client.username)
        r = bill_namespace.create_app(app2)
        self.assert_status_201(r)

    def test_required(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        params = ['path', 'name', 'visibility', 'install_slug', 'enable_os']
        for param in params:
            app = self.chrome_app()
            del app[param]
            r = namespace.create_app(app)
            self.assert_status_400(r)

    def test_enable_os(self):
        case_list = [
            {
                "enable_os": [],
                "status": 400
            }, {
                "enable_os": "iOS",
                "status": 400
            }, {
                "enable_os": ["xyz"],
                "status": 400
            }, {
                "enable_os": ["iOS", "xyz"],
                "status": 400
            }, {
                "enable_os": ["iOS", "Android", "macOS", "Windows", "Linux", "tvOS"],
                "status": 201
            }
        ]
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        for case in case_list:
            app = self.chrome_app()
            app['enable_os'] = case['enable_os']
            r = namespace.create_app(app)
            self.assert_status(r, case['status'])

    def test_invalid_name(self):
        # 0 < len(name) <= 128
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()

        max_length = 128
        app['name'] = 'a' * max_length
        r = namespace.create_app(app)
        self.assert_status_201(r)

        app['name'] = 'a' * max_length + 'a'
        r = namespace.create_app(app)
        self.assert_status_400(r)

        app['name'] = ''
        r = namespace.create_app(app)
        self.assert_status_400(r)

    def test_visibility(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()

        app['visibility'] = 'a'
        r = namespace.create_app(app)
        self.assert_status_400(r)

        allow_visibility = ['Private', 'Internal', 'Public']
        for visibility in allow_visibility:
            app = self.chrome_app()
            app['path'] += visibility
            app['visibility'] = visibility
            app['install_slug'] += visibility
            r = namespace.create_app(app)
            self.assert_status_201(r)

    def test_delete_app(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)

        app_api = namespace.get_app_api(app['path'])

        r = app_api.remove_app()
        self.assert_status_204(r)

        r = app_api.get_app()
        self.assert_status_404(r)



class UserUniversalAppCreate2Test(BaseTestCase):

    def create_and_get_user(self, username='LarryPage', auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def kind(self):
        return 'User'

    def suffix_namespace(self, namespace):
        return namespace

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

    def test_duplicate_install_slug(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        namespace.create_app(app)

        app2 = self.todo_app()
        app2['install_slug'] = app['install_slug']
        r =  namespace.create_app(app2)
        self.assert_status_409(r)

        bill: Api = self.create_and_get_user('BillGates')
        bill_namespace = self.create_and_get_namespace(bill, bill.client.username)
        r = bill_namespace.create_app(app2)
        self.assert_status_409(r)

        org_namespace = self.create_and_get_org_namespace(bill, 'microsoft')
        r = org_namespace.create_app(app2)
        self.assert_status_409(r)

        app3 = self.todo_app()
        r = org_namespace.create_app(app3)
        self.assert_status_201(r)

        r =  namespace.create_app(app3)
        self.assert_status_409(r)

    def test_create_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        r = namespace.get_my_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        anonymous: Api = Api(UnitTestClient())
        anonymous_namespace = self.create_and_get_namespace(anonymous, anonymous.client.username)
        app = self.todo_app()
        r = anonymous_namespace.create_app(app)
        self.assert_status_401(r)

    def test_remove_public_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Public')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)

    def test_remove_internal_org_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Internal')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)

    def test_remove_private_org_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username, visibility='Private')
        app = self.chrome_app(visibility='Private')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)


class OrganizationUniversalAppCreateTest(UserUniversalAppCreateTest):

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
        api.get_org_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_org_api(namespace).get_app_api(app_path)

    def test_create_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_namespace = anonymous.get_org_api('LarryPage')
        app = self.todo_app()
        r = anonymous_namespace.create_app(app)
        self.assert_status_401(r)

    def test_remove_public_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Public')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)

    def test_remove_internal_org_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Internal')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)

    def test_remove_private_org_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username, visibility='Private')
        app = self.chrome_app(visibility='Private')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Developer')
        self.assert_status_201(r)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        r = app_api.change_member_role('BillGates', 'Tester')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.remove_app()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.remove_app()
        self.assert_status_401(r)

        r = app_api.change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill_app_api.remove_app()
        self.assert_status_204(r)
