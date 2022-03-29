from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

class OrganizationListTest(BaseTestCase):

    def create_org(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.google_org()

        r = api.get_user_api().create_org(org)
        self.assert_status_201(r)

        path = org['path']
        return api.get_org_api(path)

    def test_empty_orgs(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        r = api.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)

    def test_less_than_one_page(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        user_api = api.get_user_api()
        number = 6
        for i in range(number):
            org = self.generate_org(i)
            r = user_api.create_org(org)
            self.assert_status_201(r)
        r = user_api.get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, number)

    def test_more_than_one_page(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        anonymous: Api = Api(UnitTestClient())
        user_api = api.get_user_api()
        number = 36
        org_list = []
        for i in range(number):
            org = self.generate_org(i, 'Public')
            org_list.append(org)
            r = user_api.create_org(org)
            self.assert_status_201(r)

        r = user_api.get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list = self.get_resp_list(r)
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_org_list[i], org_list[i], ['name'])
            self.assert_partial_dict_equal(resp_org_list2[i], org_list[i], ['name'])
            
        r = user_api.get_visible_org_list(page=2, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list = self.get_resp_list(r)
        r = anonymous.get_user_api().get_visible_org_list(page=2, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_org_list[i], org_list[i+10], ['name'])
            self.assert_partial_dict_equal(resp_org_list2[i], org_list[i+10], ['name'])

        r = user_api.get_visible_org_list(page=3, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list = self.get_resp_list(r)
        r = anonymous.get_user_api().get_visible_org_list(page=3, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 10)
        resp_org_list2 = self.get_resp_list(r)
        for i in range(10):
            self.assert_partial_dict_equal(resp_org_list[i], org_list[i+20], ['name'])
            self.assert_partial_dict_equal(resp_org_list2[i], org_list[i+20], ['name'])

        r = user_api.get_visible_org_list(page=4, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 6)
        resp_org_list = self.get_resp_list(r)
        r = anonymous.get_user_api().get_visible_org_list(page=4, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 6)
        resp_org_list2 = self.get_resp_list(r)
        for i in range(6):
            self.assert_partial_dict_equal(resp_org_list[i], org_list[i+30], ['name'])
            self.assert_partial_dict_equal(resp_org_list2[i], org_list[i+30], ['name'])

        r = user_api.get_visible_org_list(page=5, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 0)
        r = anonymous.get_user_api().get_visible_org_list(page=5, per_page=10)
        self.assert_status_200(r)
        self.assert_list_length(r, 0)

        r = user_api.get_visible_org_list(page=-1, per_page=10)
        self.assert_status_400(r)

        r = user_api.get_visible_org_list(page=1, per_page=101)
        self.assert_status_400(r)

        r = user_api.get_visible_org_list(page=1, per_page=-1)
        self.assert_status_400(r)

        r = user_api.get_visible_org_list(page='a', per_page=10)
        self.assert_status_400(r)

        r = user_api.get_visible_org_list(page=1, per_page='a')
        self.assert_status_400(r)

        r = user_api.get_visible_org_list(page=1, per_page=100)
        self.assert_status_200(r)

    def test_multi_org_multi_member(self):
        larry: Api = Api(UnitTestClient(), 'LarryPage', True)
        org1 = self.generate_org(1, 'Public')
        larry.get_user_api().create_org(org1)
        org2 = self.generate_org(2, 'Private')
        larry.get_user_api().create_org(org2)
        org3 = self.generate_org(3, 'Private')
        larry.get_user_api().create_org(org3)
        org4 = self.generate_org(4, 'Internal')
        larry.get_user_api().create_org(org4)

        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        org11 = self.generate_org(11, 'Public')
        bill.get_user_api().create_org(org11)
        org12 = self.generate_org(12, 'Private')
        bill.get_user_api().create_org(org12)
        org13 = self.generate_org(13, 'Private')
        bill.get_user_api().create_org(org13)
        org14 = self.generate_org(14, 'Internal')
        bill.get_user_api().create_org(org14)

        mark: Api = Api(UnitTestClient(), 'Mark', True)
        org21 = self.generate_org(21, 'Public')
        mark.get_user_api().create_org(org21)

        larry.get_org_api(org1['path']).add_member(bill.client.username, 'Member')
        larry.get_org_api(org2['path']).add_member(bill.client.username, 'Member')

        bill.get_org_api(org11['path']).add_member(larry.client.username, 'Member')
        bill.get_org_api(org12['path']).add_member(larry.client.username, 'Member')

        bill.get_org_api(org11['path']).add_member(mark.client.username, 'Member')
        bill.get_org_api(org12['path']).add_member(mark.client.username, 'Member')

        r = larry.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 8)
        resp_list = self.get_resp_list(r)
        expect_org_info = {
            org1['path']: 'Admin',
            org2['path']: 'Admin',
            org3['path']: 'Admin',
            org4['path']: 'Admin',
            org11['path']: 'Member',
            org12['path']: 'Member',
            org14['path']: None,
            org21['path']: None
        }
        resp_org_info = dict([(org['path'], org.get('role', None)) for org in resp_list])
        self.assertDictEqual(resp_org_info, expect_org_info)

        r = bill.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 8)
        resp_list = self.get_resp_list(r)
        expect_org_info = {
            org11['path']: 'Admin',
            org12['path']: 'Admin',
            org13['path']: 'Admin',
            org14['path']: 'Admin',
            org1['path']: 'Member',
            org2['path']: 'Member',
            org4['path']: None,
            org21['path']: None
        }
        resp_org_info = dict([(org['path'], org.get('role', None)) for org in resp_list])
        self.assertDictEqual(resp_org_info, expect_org_info)

        r = mark.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 6)
        resp_list = self.get_resp_list(r)
        expect_org_info = {
            org1['path']: None,
            org4['path']: None,
            org11['path']: 'Member',
            org12['path']: 'Member',
            org21['path']: 'Admin',
            org14['path']: None
        }
        resp_org_info = dict([(org['path'], org.get('role', None)) for org in resp_list])
        self.assertDictEqual(resp_org_info, expect_org_info)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_list_length(r, 3)
        resp_list = self.get_resp_list(r)
        expect_org_info = {
            org1['path']: None,
            org11['path']: None,
            org21['path']: None
        }
        resp_org_info = dict([(org['path'], org.get('role', None)) for org in resp_list])
        self.assertDictEqual(resp_org_info, expect_org_info)

    def test_order_by(self):
        pass

    def test_filter(self):
        pass

    def test_get_public_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Public')
        path = org['path']
        api.get_user_api().create_org(org)
        
        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = mark.get_org_api(path).get_org()
        self.assert_status_200(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_200(r)

    def test_get_internal_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Internal')
        path = org['path']
        api.get_user_api().create_org(org)
        
        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = mark.get_org_api(path).get_org()
        self.assert_status_200(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_404(r)

    def test_get_private_org_permission(self):
        api: Api = Api(UnitTestClient(), 'LarryPage', True)
        org = self.generate_org(1, 'Private')
        path = org['path']
        api.get_user_api().create_org(org)
        
        bill: Api = Api(UnitTestClient(), 'BillGates', True)
        api.get_org_api(path).add_member('BillGates', 'Admin')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Collaborator')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        api.get_org_api(path).change_member_role('BillGates', 'Member')
        r = bill.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)
        r = bill.get_org_api(path).get_org()
        self.assert_status_200(r)

        mark: Api = Api(UnitTestClient(), 'MarkZuckerberg', True)
        r = mark.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)
        r = mark.get_org_api(path).get_org()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        r = anonymous.get_user_api().get_visible_org_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)
        r = anonymous.get_org_api(path).get_org()
        self.assert_status_404(r)
