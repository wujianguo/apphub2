from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserUniversalAppMemberTest(BaseTestCase):
    def create_and_get_user(self, username="LarryPage", auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        return api.get_user_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_user_api(namespace).get_app_api(app_path)

    def test_add_member(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app(visibility="Private")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.get_member("xyz")
        self.assert_status_404(r)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.get_app()
        self.assert_status_404(r)

        r = app_api.add_member("BillGates", "xyz")
        self.assert_status_400(r)
        r = app_api.add_member("jackxxx", "Developer")
        self.assert_status_400(r)
        r = app_api.add_member("BillGates", "Developer")
        self.assert_status_201(r)
        r = app_api.get_member("BillGates")
        self.assert_status_200(r)
        self.assertEqual(r.json()["username"], "BillGates")
        self.assertEqual(r.json()["role"], "Developer")

        r = app_api.add_member("BillGates", "Developer")
        self.assert_status_409(r)

        r = bill_app_api.get_app()
        self.assert_status_200(r)
        # todo
        # self.assertEqual(r.json()['role'], 'Developer')
        r = bill.get_user_api().get_visible_app_list()
        self.assert_list_length(r, 1)


class UserUniversalAppMember2Test(BaseTestCase):
    def kind(self):
        return "User"

    def suffix_namespace(self, namespace):
        return namespace

    def create_and_get_user(self, username="LarryPage", auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def get_app_api(self, api, namespace, app_path):
        return api.get_user_api(namespace).get_app_api(app_path)

    def test_modify_member_role(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(
            larry, larry.client.username
        )  # , visibility='Private')
        app = self.chrome_app(visibility="Private")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.change_member_role("LarryPage", "xyz")
        self.assert_status_400(r)

        r = app_api.change_member_role("LarryPage", "Developer")
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.get_app()
        self.assert_status_404(r)

        r = app_api.add_member("BillGates", "Manager")
        self.assert_status_201(r)
        r = bill_app_api.get_app()
        self.assert_status_200(r)
        # todo
        # self.assertEqual(r.json()['role'], 'Manager')
        r = app_api.change_member_role("BillGates", "Developer")
        self.assert_status_200(r)
        r = bill_app_api.change_or_set_icon()
        self.assert_status_403(r)
        r = bill_app_api.change_member_role("BillGates", "Manager")
        self.assert_status_403(r)
        r = bill_app_api.change_member_role("LarryPage", "Developer")
        self.assert_status_403(r)

        r = app_api.change_member_role("BillGates", "Tester")
        self.assert_status_200(r)
        r = bill_app_api.change_or_set_icon()
        self.assert_status_403(r)
        r = bill_app_api.change_member_role("BillGates", "Manager")
        self.assert_status_403(r)
        r = bill_app_api.change_member_role("LarryPage", "Developer")
        self.assert_status_403(r)

        r = app_api.change_member_role("BillGates", "Manager")
        self.assert_status_200(r)

        r = bill_app_api.change_or_set_icon()
        self.assert_status_204(r)
        r = bill_app_api.change_member_role("LarryPage", "Developer")
        self.assert_status_403(r)

    def test_remove_member(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(
            larry, larry.client.username
        )  # , visibility='Private')
        app = self.chrome_app(visibility="Private")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.remove_member("LarryPage")
        self.assert_status_403(r)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        r = bill_app_api.get_app()
        self.assert_status_404(r)

        r = app_api.add_member("BillGates", "Manager")
        self.assert_status_201(r)
        r = app_api.get_member("BillGates")
        self.assert_status_200(r)

        r = bill_app_api.get_app()
        self.assert_status_200(r)

        r = app_api.remove_member("BillGates")
        self.assert_status_204(r)

        r = bill_app_api.get_app()
        self.assert_status_404(r)

    def test_get_public_member_permissions(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(
            larry, larry.client.username
        )  # , visibility='Private')
        app = self.chrome_app(visibility="Public")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        app_api.add_member("BillGates", "Manager")

        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Developer")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Tester")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), "MarkZuckerberg", True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = mark_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = anonymous_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

    def test_get_internal_member_permissions(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(
            larry, larry.client.username
        )  # , visibility='Private')
        app = self.chrome_app(visibility="Internal")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        app_api.add_member("BillGates", "Manager")

        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Developer")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Tester")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), "MarkZuckerberg", True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = mark_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.get_member("LarryPage")
        self.assert_status_404(r)
        r = anonymous_app_api.get_member_list()
        self.assert_status_404(r)

    def test_get_private_member_permissions(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(
            larry, larry.client.username
        )  # , visibility='Private')
        app = self.chrome_app(visibility="Private")
        r = namespace.create_app(app)
        self.assert_status_201(r)
        path = app["path"]

        app_api = self.get_app_api(larry, larry.client.username, path)

        r = app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        bill: Api = Api(UnitTestClient(), "BillGates", True)
        bill_app_api = self.get_app_api(bill, larry.client.username, path)
        app_api.add_member("BillGates", "Manager")

        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Developer")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        app_api.change_member_role("BillGates", "Tester")
        r = bill_app_api.get_member("LarryPage")
        self.assert_status_200(r)
        r = bill_app_api.get_member_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 2)

        mark: Api = Api(UnitTestClient(), "MarkZuckerberg", True)
        mark_app_api = self.get_app_api(mark, larry.client.username, path)
        r = mark_app_api.get_member("LarryPage")
        self.assert_status_404(r)
        r = mark_app_api.get_member_list()
        self.assert_status_404(r)

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_app_api(anonymous, larry.client.username, path)
        r = anonymous_app_api.get_member("LarryPage")
        self.assert_status_404(r)
        r = anonymous_app_api.get_member_list()
        self.assert_status_404(r)


class OrganizationUniversalAppMemberTest(UserUniversalAppMemberTest):
    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        org = self.generate_org(1, visibility=visibility)
        org["path"] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org["path"])

    def get_app_api(self, api, namespace, app_path):
        return api.get_org_api(namespace).get_app_api(app_path)
