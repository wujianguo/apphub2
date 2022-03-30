import tempfile
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

def skip_if_base(func):
    def wrap(self, *args, **kwargs):
        if not self.kind():
            self.skipTest('skip base.')
            return
        return func(self, *args, **kwargs)
    return wrap

class BaseUniversalAppUpdateTest(BaseTestCase):

    def kind(self):
        return ''

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        pass

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

    @skip_if_base
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

class UserUniversalAppUpdateTest(BaseUniversalAppUpdateTest):

    def kind(self):
        return 'User'

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

class OrganizationUniversalAppUpdateTest(BaseUniversalAppUpdateTest):

    def kind(self):
        return 'Organization'

    def create_and_get_namespace(self, api, namespace):
        org = self.generate_org(1)
        org['path'] = namespace + '_org'
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])
