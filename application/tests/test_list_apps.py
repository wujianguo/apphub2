from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase

def skip_if_base(func):
    def wrap(self, *args, **kwargs):
        if not self.kind():
            return
        return func(self, *args, **kwargs)
    return wrap

class BaseUniversalAppListTest(BaseTestCase):

    def kind(self):
        return ''

    def create_and_get_user(self, username='LarryPage'):
        return Api(UnitTestClient(), username, True)

    def create_and_get_namespace(self, api, namespace):
        pass

    @skip_if_base
    def xtest_empty_orgs(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)

        r = namespace.get_app_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 0)

class UserUniversalAppListTest(BaseUniversalAppListTest):

    def kind(self):
        return 'User'

    def create_and_get_namespace(self, api, namespace):
        return api.get_user_api(namespace)


class OrganizationUniversalAppListTest(BaseUniversalAppListTest):

    def kind(self):
        return 'Organization'

    def create_and_get_namespace(self, api, namespace):
        org = self.generate_org(1)
        org['path'] = namespace + '_org'
        api.get_user_api().create_org(org)
        return api.get_org_api(org['path'])
