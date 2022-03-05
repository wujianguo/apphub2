from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class OrganizationMemberTest(BaseTestCase):

    def create_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        path = org['path']
        return api.get_org_api(path)

    def test_add_member(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org('Private')
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)
        path = org['path']
        org_api = api.get_org_api(path)

        r = org_api.get_member('xyz')
        self.assert_status_404(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        r = bill.get_org_api(path).get_org()
        self.assert_status_404(r)

        r = org_api.add_member('BillGates', 'xyz')
        self.assert_status_400(r)
        r = org_api.add_member('jackxxx', 'Collaborator')
        self.assert_status_400(r)
        r = org_api.add_member('BillGates', 'Collaborator')
        self.assert_status_201(r)
        r = org_api.get_member('BillGates')
        self.assert_status_200(r)
        self.assertEqual(r.json()['username'], 'BillGates')
        self.assertEqual(r.json()['role'], 'Collaborator')

        r = org_api.add_member('BillGates', 'Collaborator')
        self.assert_status_409(r)

        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)
        self.assertEqual(r.json()['role'], 'Collaborator')
        r = bill.get_user_api().get_org_list()
        self.assert_list_length(r, 1)

    def test_modify_member_role(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org('Private')
        api.get_user_api().create_org(org)
        path = org['path']
        org_api = api.get_org_api(path)

        r = org_api.change_member_role('LarryPage', 'xyz')
        self.assert_status_400(r)

        r = org_api.change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        r = bill.get_org_api(path).get_org()
        self.assert_status_404(r)

        r = org_api.add_member('BillGates', 'Admin')
        self.assert_status_201(r)
        r = bill.get_org_api(path).get_org()
        self.assertEqual(r.json()['role'], 'Admin')
        r = org_api.change_member_role('BillGates', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_or_set_icon()
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('BillGates', 'Admin')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)

        r = org_api.change_member_role('BillGates', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_or_set_icon()
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('BillGates', 'Admin')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)

        r = org_api.change_member_role('BillGates', 'Admin')
        self.assert_status_200(r)

        r = bill.get_org_api(path).change_or_set_icon()
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)

    def test_remove_member(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org('Private')
        api.get_user_api().create_org(org)
        path = org['path']
        org_api = api.get_org_api(path)

        r = org_api.remove_member('LarryPage')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        r = bill.get_org_api(path).get_org()
        self.assert_status_404(r)

        r = org_api.add_member('BillGates', 'Admin')
        self.assert_status_201(r)
        r = org_api.get_member('BillGates')
        self.assert_status_200(r)

        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        r = bill.get_org_api(path).remove_member('LarryPage')
        self.assert_status_204(r)

        r = org_api.get_org()
        self.assert_status_404(r)

        r = bill.get_org_api(path).add_member('LarryPage', 'Admin')
        self.assert_status_201(r)

        r = api.get_org_api(path).remove_member('LarryPage')
        self.assert_status_204(r)

    def test_get_public_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        r = api.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = api.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = mark.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = anonymous.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

    def test_get_internal_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        r = api.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = api.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = mark.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_member('LarryPage')
        self.assert_status_404(r)
        r = anonymous.get_org_api(path).get_member_list()
        self.assert_status_404(r)

    def test_get_private_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        r = api.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = api.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).get_member('LarryPage')
        self.assert_status_200(r)
        r = bill.get_org_api(path).get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).get_member('LarryPage')
        self.assert_status_404(r)
        r = mark.get_org_api(path).get_member_list()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).get_member('LarryPage')
        self.assert_status_404(r)
        r = anonymous.get_org_api(path).get_member_list()
        self.assert_status_404(r)

    def test_add_public_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        Api(UnitTestClient(), 'member_admin', True)
        r = bill.get_org_api(path).add_member('member_admin', 'Admin')
        self.assert_status_201(r)
        member_collaborator: Api = Api(UnitTestClient(), 'member_collaborator', True)
        r = bill.get_org_api(path).add_member('member_collaborator', 'Collaborator')
        self.assert_status_201(r)
        member_member: Api = Api(UnitTestClient(), 'member_member', True)
        r = bill.get_org_api(path).add_member('member_member', 'Member')
        self.assert_status_201(r)

        Api(UnitTestClient(), 'member2', True)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        Api(UnitTestClient(), 'member3', True)
        r = member_member.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        member_internal: Api = Api(UnitTestClient(), 'member_internal', True)
        r = member_internal.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_401(r)

    def test_add_internal_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        Api(UnitTestClient(), 'member_admin', True)
        r = bill.get_org_api(path).add_member('member_admin', 'Admin')
        self.assert_status_201(r)
        member_collaborator: Api = Api(UnitTestClient(), 'member_collaborator', True)
        r = bill.get_org_api(path).add_member('member_collaborator', 'Collaborator')
        self.assert_status_201(r)
        member_member: Api = Api(UnitTestClient(), 'member_member', True)
        r = bill.get_org_api(path).add_member('member_member', 'Member')
        self.assert_status_201(r)

        Api(UnitTestClient(), 'member2', True)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        Api(UnitTestClient(), 'member3', True)
        r = member_member.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        member_internal: Api = Api(UnitTestClient(), 'member_internal', True)
        r = member_internal.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_401(r)

    def test_add_private_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')

        Api(UnitTestClient(), 'member_admin', True)
        r = bill.get_org_api(path).add_member('member_admin', 'Admin')
        self.assert_status_201(r)
        member_collaborator: Api = Api(UnitTestClient(), 'member_collaborator', True)
        r = bill.get_org_api(path).add_member('member_collaborator', 'Collaborator')
        self.assert_status_201(r)
        member_member: Api = Api(UnitTestClient(), 'member_member', True)
        r = bill.get_org_api(path).add_member('member_member', 'Member')
        self.assert_status_201(r)

        Api(UnitTestClient(), 'member2', True)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_collaborator.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        Api(UnitTestClient(), 'member3', True)
        r = member_member.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_403(r)
        r = member_member.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_403(r)

        member_internal: Api = Api(UnitTestClient(), 'member_internal', True)
        r = member_internal.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_404(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_404(r)
        r = member_internal.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).add_member('member2', 'Admin')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Collaborator')
        self.assert_status_401(r)
        r = anonymous.get_org_api(path).add_member('member2', 'Member')
        self.assert_status_401(r)

    def test_change_public_member_role_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        api.get_user_api().create_org(org)

        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Collaborator')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)

        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).remove_member('BillGates')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_401(r)

    def test_change_internal_member_role_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        api.get_user_api().create_org(org)

        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Collaborator')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)

        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).remove_member('BillGates')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_401(r)

    def test_change_private_member_role_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        api.get_user_api().create_org(org)

        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Collaborator')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = api.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)
        r = api.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)

        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_403(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Member')
        self.assert_status_200(r)
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Admin')
        self.assert_status_200(r)

        api.get_org_api(path).remove_member('BillGates')
        r = bill.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).change_member_role('LarryPage', 'Collaborator')
        self.assert_status_401(r)

    def test_remove_member_permissions(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        api.get_user_api().create_org(org)

        r = api.get_org_api(path).remove_member('LarryPage')
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Collaborator')
        r = bill.get_org_api(path).remove_member('LarryPage')
        self.assert_status_403(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_org_api(path).remove_member('LarryPage')
        self.assert_status_403(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_org_api(path).remove_member('LarryPage')
        self.assert_status_403(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_org_api(path).remove_member('LarryPage')
        self.assert_status_401(r)

        api.get_org_api(path).change_member_role('BillGates', 'Admin')
        r = bill.get_org_api(path).remove_member('LarryPage')
        self.assert_status_204(r)
