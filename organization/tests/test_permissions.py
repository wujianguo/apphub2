from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class OrganizationPermissionTest(BaseTestCase):

    def test_org_visibility(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        api.get_user_api().create_org(org)

        org = self.generate_org(2, 'Internal')
        api.get_user_api().create_org(org)

        org = self.generate_org(3, 'Public')
        api.get_user_api().create_org(org)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        r = bill.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 2)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 1)

    def test_member_can_view_private_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        api.get_user_api().create_org(org)
        path = org['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Member')
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_404(r)

    def test_internal_can_view_internal_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        api.get_user_api().create_org(org)
        path = org['path']

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_404(r)

    def test_anonymous_can_view_public_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        api.get_user_api().create_org(org)
        path = org['path']

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_200(r)

    def test_anonymous_can_not_modify_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        api.get_user_api().create_org(org)
        path = org['path']

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_200(r)
        r = anonymous.get_org_api(path).change_or_set_icon()
        self.assert_status_401(r)
