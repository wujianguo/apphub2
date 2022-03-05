import tempfile
from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class OrganizationUpdateTest(BaseTestCase):

    def create_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        path = org['path']
        return api.get_org_api(path)

    def test_modify_org_path(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()

        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        old_value = r.json()

        path = org['path']

        new_path = 'new_path'
        data = {'path': new_path}
        org_api = api.get_org_api(path)
        r = org_api.update_org(data)
        self.assert_status_200(r)

        r = org_api.get_org()
        self.assert_status_404(r)

        org['path'] = 'about'
        r = api.get_org_api(new_path).update_org(org)
        self.assert_status_409(r)

        r = api.get_org_api(new_path).get_org()
        self.assert_status_200(r)

        old_value['path'] = new_path
        del old_value['update_time']
        new_value = r.json()
        del new_value['update_time']
        self.assertDictEqual(new_value, old_value)

    def test_modify_invalid_path(self):
        # 1. only letters, numbers, underscores or hyphens
        # 2. 0 < len(path) <= 32
        org_api = self.create_org()

        max_length = 32
        new_path = 'a' * max_length + 'a'
        r = org_api.update_org({'path': new_path})
        self.assert_status_400(r)

        new_path = ''
        r = org_api.update_org({'path': new_path})
        self.assert_status_400(r)

        new_path = 'a' * max_length
        r = org_api.update_org({'path': new_path})
        self.assert_status_200(r)

    def test_modify_duplicate_path(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()

        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        path = org['path']
        org_api = api.get_org_api(path)

        path = org['path']
        r = org_api.update_org({'path': path})
        self.assert_status_200(r)

        org2 = self.microsoft_org()
        r = api.get_user_api().create_org(org2)
        self.assert_status_201(r)
        new_path = org2['path']
        r = org_api.update_org({'path': new_path})
        self.assert_status_409(r)

    def test_modify_org_name(self):
        org_api = self.create_org()

        max_length = 128
        name = 'a' * max_length
        r = org_api.update_org({'name': name})
        self.assert_status_200(r)

        name = 'a' * max_length + 'a'
        r = org_api.update_org({'name': name})
        self.assert_status_400(r)

        name = ''
        r = org_api.update_org({'name': name})
        self.assert_status_400(r)

    def test_modify_org_visibility(self):
        org_api = self.create_org()

        visibility = 'a'
        r = org_api.update_org({'visibility': visibility})
        self.assert_status_400(r)

        allow_visibility = ['Private', 'Internal', 'Public']
        for visibility in allow_visibility:
            visibility = visibility
            r = org_api.update_org({'visibility': visibility})
            self.assert_status_200(r)

    def test_upload_icon(self):
        org_api = self.create_org()

        r1 = org_api.get_icon()
        self.assert_status_404(r1)

        r = org_api.change_or_set_icon()
        self.assert_status_200(r)
        self.assertNotEqual(r.json()['icon_file'], '')

        r1 = org_api.get_icon()
        self.assert_status_200(r)

        r2 = org_api.change_or_set_icon()
        self.assert_status_200(r2)
        # self.assertNotEqual(r2.json()['icon_file'], r.json()['icon_file'])
        # self.assertNotEqual(r2.json()['icon_file'], '')

        file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.write(b'hello')
        file_path = file.name
        r = org_api.change_or_set_icon(file_path)
        self.assert_status_400(r)

    def test_delete_icon(self):
        org_api = self.create_org()

        r = org_api.change_or_set_icon()
        self.assert_status_200(r)

        r = org_api.remove_icon()
        self.assert_status_204(r)

        # todo
        # r = org_api.get_org()
        # self.assertEqual(r.json()['icon_file'], '')

    def test_update_public_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        update_org = {'description': 'My description.'}
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).update_org(update_org)
        self.assert_status_401(r)

    def test_update_internal_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        update_org = {'description': 'My description.'}
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).update_org(update_org)
        self.assert_status_401(r)

    def test_update_private_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        update_org = {'description': 'My description.'}
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).update_org(update_org)
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).update_org(update_org)
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).update_org(update_org)
        self.assert_status_401(r)
