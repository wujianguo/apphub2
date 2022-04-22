from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class OrganizationCreateTest(BaseTestCase):

    def create_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        path = org['path']
        return api.get_org_api(path)

    def test_create_success(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        self.assert_partial_dict_equal(org, r.json(), ['path', 'name', 'visibility', 'description'])
        path = org['path']

        r2 = api.get_org_api(path).get_org()
        self.assertDictEqual(r.json(), r2.json())
        rr = api.get_or_head_file(r2.json()['icon_file'])
        self.assert_status_200(rr)

        r3 = api.get_user_api().get_visible_org_list()
        self.assertDictEqual(self.get_resp_list(r3)[0], r.json())

    def test_invalid_path(self):
        # 1. only letters, numbers, underscores or hyphens
        # 2. 0 < len(path) <= 32
        # 3. reserved
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        org['path'] += '*'
        user_api = api.get_user_api()
        r = user_api.create_org(org)
        self.assert_status_400(r)

        max_length = 32
        org['path'] = 'a' * max_length
        r = user_api.create_org(org)
        self.assert_status_201(r)

        org['path'] = 'a' * max_length + 'a'
        r = user_api.create_org(org)
        self.assert_status_400(r)

        org['path'] = ''
        r = user_api.create_org(org)
        self.assert_status_400(r)

        del org['path']
        r = user_api.create_org(org)
        self.assert_status_400(r)

        org['path'] = 'about'
        r = user_api.create_org(org)
        self.assert_status_409(r)

    def test_duplicate_path(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        api.get_user_api().create_org(org)

        org2 = self.microsoft_org()
        org2['path'] = org['path']
        r =  api.get_user_api().create_org(org2)
        self.assert_status_409(r)

    def test_required(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        del org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)
        
        org = self.google_org()
        del org['name']
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)

        org = self.google_org()
        del org['visibility']
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)

    def test_invalid_name(self):
        # 0 < len(name) <= 128
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()

        max_length = 128
        org['name'] = 'a' * max_length
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        org['name'] = 'a' * max_length + 'a'
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)

        org['name'] = ''
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)

    def test_visibility(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()

        org['visibility'] = 'a'
        r = api.get_user_api().create_org(org)
        self.assert_status_400(r)

        allow_visibility = ['Private', 'Internal', 'Public']
        for visibility in allow_visibility:
            org = self.google_org()
            org['path'] += visibility
            org['visibility'] = visibility
            r = api.get_user_api().create_org(org)
            self.assert_status_201(r)

    def test_delete_org(self):
        org_api = self.create_org()
        app = self.chrome_app()
        org_api.create_app(app)

        r = org_api.remove_org()
        self.assert_status_403(r)

        org_api.get_app_api(app['path']).remove_app()

        r = org_api.remove_org()
        self.assert_status_204(r)

        r = org_api.get_org()
        self.assert_status_404(r)

    def test_create_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1)
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        anonymous: Api = Api(UnitTestClient())
        org = self.generate_org(2)
        r = anonymous.get_user_api().create_org(org)
        self.assert_status_401(r)

    def test_remove_public_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Developer')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Tester')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).remove_org()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).remove_org()
        self.assert_status_401(r)

        r = api.get_org_api(path).change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).remove_member('BillGates')
        r = api.get_org_api(path).remove_org()
        self.assert_status_204(r)

    def test_remove_internal_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Developer')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Tester')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).remove_org()
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).remove_org()
        self.assert_status_401(r)

        r = api.get_org_api(path).change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).remove_member('BillGates')
        r = api.get_org_api(path).remove_org()
        self.assert_status_204(r)

    def test_remove_private_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Developer')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Tester')
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).remove_org()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).remove_org()
        self.assert_status_401(r)

        r = api.get_org_api(path).change_member_role('BillGates', 'Manager')
        self.assert_status_200(r)
        r = bill.get_org_api(path).remove_org()
        self.assert_status_403(r)

        api.get_org_api(path).remove_member('BillGates')
        r = api.get_org_api(path).remove_org()
        self.assert_status_204(r)
