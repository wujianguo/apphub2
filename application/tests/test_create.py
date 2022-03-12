from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

def skip_if_base(func):
    def wrap(self, *args, **kwargs):
        if not self.kind():
            return
        return func(self, *args, **kwargs)
    return wrap

class BaseUniversalAppCreateTest(BaseTestCase):

    def kind(self):
        return ''

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        pass

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
    def test_required(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        params = ['path', 'name', 'visibility', 'install_slug', 'enable_os']
        for param in params:
            app = self.chrome_app()
            del app[param]
            r = namespace.create_app(app)
            self.assert_status_400(r)

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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


class UserUniversalAppCreateTest(BaseUniversalAppCreateTest):

    def kind(self):
        return 'User'

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def test_create_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_namespace = self.create_and_get_namespace(anonymous, anonymous.client.username)
        app = self.todo_app()
        r = anonymous_namespace.create_app(app)
        self.assert_status_401(r)


class OrganizationUniversalAppCreateTest(BaseUniversalAppCreateTest):

    def kind(self):
        return 'Organization'

    def create_and_get_namespace(self, api, namespace):
        org = self.generate_org(1)
        org['path'] = namespace + '_org'
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])

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
