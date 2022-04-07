import tempfile
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserUniversalAppUpdateTest(BaseTestCase):

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

    def test_modify_app_path(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        old_value = r.json()
        path = app['path']

        r = namespace.get_app_api(path).get_app()
        self.assert_status_200(r)

        new_path = 'new_path'
        data = {'path': new_path}
        app_api = namespace.get_app_api(path)
        r = app_api.update_app(data)
        self.assert_status_200(r)

        r = app_api.get_app()
        self.assert_status_404(r)

        app['path'] = 'about'
        r = namespace.get_app_api(new_path).update_app(app)
        self.assert_status_409(r)

        r = namespace.get_app_api(new_path).get_app()
        self.assert_status_200(r)

        old_value['path'] = new_path
        del old_value['update_time']
        new_value = r.json()
        del new_value['update_time']
        self.assertDictEqual(new_value, old_value)

    def test_modify_invalid_path(self):
        # 1. only letters, numbers, underscores or hyphens
        # 2. 0 < len(path) <= 32
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        max_length = 32
        new_path = 'a' * max_length + 'a'
        r = app_api.update_app({'path': new_path})
        self.assert_status_400(r)

        new_path = ''
        r = app_api.update_app({'path': new_path})
        self.assert_status_400(r)

        new_path = 'a' * max_length
        r = app_api.update_app({'path': new_path})
        self.assert_status_200(r)

    def test_modify_duplicate_path(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        path = app['path']
        r = app_api.update_app({'path': path})
        self.assert_status_200(r)

        app2 = self.todo_app()
        r = namespace.create_app(app2)
        self.assert_status_201(r)
        new_path = app2['path']
        r = app_api.update_app({'path': new_path})
        self.assert_status_409(r)

    def test_modify_duplicate_install_slug(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        install_slug = app['install_slug']
        r = app_api.update_app({'install_slug': install_slug})
        self.assert_status_200(r)

        app2 = self.todo_app()
        r = namespace.create_app(app2)
        self.assert_status_201(r)
        install_slug = app2['install_slug']
        r = app_api.update_app({'install_slug': install_slug})
        self.assert_status_409(r)

    def test_modify_app_name(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        max_length = 128
        name = 'a' * max_length
        r = app_api.update_app({'name': name})
        self.assert_status_200(r)

        name = 'a' * max_length + 'a'
        r = app_api.update_app({'name': name})
        self.assert_status_400(r)

        name = ''
        r = app_api.update_app({'name': name})
        self.assert_status_400(r)

    def test_modify_app_visibility(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        visibility = 'a'
        r = app_api.update_app({'visibility': visibility})
        self.assert_status_400(r)

        allow_visibility = ['Private', 'Internal', 'Public']
        for visibility in allow_visibility:
            visibility = visibility
            r = app_api.update_app({'visibility': visibility})
            self.assert_status_200(r)

    def test_upload_icon(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        r = namespace.create_app(app)
        self.assert_status_201(r)
        app_api = namespace.get_app_api(app['path'])

        r1 = app_api.get_icon()
        self.assert_status_200(r1)

        r = app_api.change_or_set_icon()
        self.assert_status_200(r)
        self.assertNotEqual(r.json()['icon_file'], '')

        r1 = app_api.get_icon()
        self.assert_status_200(r)

        r2 = app_api.change_or_set_icon()
        self.assert_status_200(r2)
        # self.assertNotEqual(r2.json()['icon_file'], r.json()['icon_file'])
        # self.assertNotEqual(r2.json()['icon_file'], '')

        file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.write(b'hello')
        file_path = file.name
        r = app_api.change_or_set_icon(file_path)
        self.assert_status_400(r)

    def test_update_public_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Public')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Manager')
        self.assert_status_201(r)
        update_app = {'description': 'My description.'}
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.update_app(update_app)
        self.assert_status_200(r)

        app_api.change_member_role('BillGates', 'Developer')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        app_api.change_member_role('BillGates', 'Tester')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.update_app(update_app)
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.update_app(update_app)
        self.assert_status_401(r)

    def test_update_internal_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility='Internal')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Manager')
        self.assert_status_201(r)
        update_app = {'description': 'My description.'}
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.update_app(update_app)
        self.assert_status_200(r)

        app_api.change_member_role('BillGates', 'Developer')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        app_api.change_member_role('BillGates', 'Tester')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.update_app(update_app)
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.update_app(update_app)
        self.assert_status_401(r)

    def test_update_private_app_permission(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username, visibility='Private')
        app = self.chrome_app(visibility='Private')
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        app_api = self.get_app_api(larry, larry.client.username, path)
        r = app_api.add_member('BillGates', 'Manager')
        self.assert_status_201(r)
        update_app = {'description': 'My description.'}
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.update_app(update_app)
        self.assert_status_200(r)

        app_api.change_member_role('BillGates', 'Developer')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        app_api.change_member_role('BillGates', 'Tester')
        r = bill_app_api.update_app(update_app)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.update_app(update_app)
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.update_app(update_app)
        self.assert_status_401(r)

class OrganizationUniversalAppUpdateTest(UserUniversalAppUpdateTest):

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
