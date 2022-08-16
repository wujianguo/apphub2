from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class DocumentationTest(BaseTestCase):
    def test_swagger(self):
        api = Api(UnitTestClient())
        r = api.get_swagger()
        self.assert_status_200(r)
