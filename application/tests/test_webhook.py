from client.api import Api
from client.unit_test_client import UnitTestClient
from util.tests import BaseTestCase


class UserAppWebhookTest(BaseTestCase):
    def create_and_get_user(self, username="LarryPage", auto_login=True):
        return Api(UnitTestClient(), username, auto_login)

    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        return api.get_user_api(namespace)

    def get_namespace(self, api, namespace):
        return api.get_user_api(namespace)

    def test_create(self):
        larry = self.create_and_get_user()
        namespace = self.create_and_get_namespace(larry, larry.client.username)
        app = self.chrome_app()
        namespace.create_app(app)

        app_api = namespace.get_app_api(app["path"])
        webhook = {
            "name": "integration",
            "url": "https://apphub.example.com/webhook/test",
            "when_new_package": True,
            "when_new_release": True,
        }
        r = app_api.create_webhook({"url": "xyz"})
        self.assert_status_400(r)
        r = app_api.create_webhook(webhook)
        self.assert_status_201(r)
        webhook_id = r.json()["id"]

        r = app_api.get_webhook_list()
        self.assert_status_200(r)
        self.assert_list_length(r, 1)

        r = app_api.get_one_webhook(webhook_id)
        self.assert_status_200(r)

        update_webhook = {"when_new_package": False}
        r = app_api.update_webhook(webhook_id, update_webhook)
        self.assert_status_200(r)
        r = app_api.update_webhook(webhook_id, {"when_new_package": "xyz"})
        self.assert_status_400(r)

        r = app_api.get_one_webhook(webhook_id)
        self.assert_status_200(r)
        self.assertEqual(
            r.json()["when_new_package"], update_webhook["when_new_package"]
        )

        anonymous: Api = Api(UnitTestClient())
        anonymous_app_api = self.get_namespace(
            anonymous, larry.client.username
        ).get_app_api(app["path"])
        r = anonymous_app_api.get_webhook_list()
        self.assert_status_401(r)
        r = anonymous_app_api.get_one_webhook(webhook_id)
        self.assert_status_401(r)

        r = app_api.remove_webhook(webhook_id)
        self.assert_status_204(r)

        r = app_api.get_one_webhook(webhook_id)
        self.assert_status_404(r)


class OrganizationAppWebhookTest(UserAppWebhookTest):
    def create_and_get_namespace(self, api, namespace, visibility="Public"):
        org = self.generate_org(1, visibility=visibility)
        org["path"] = namespace
        api.get_user_api().create_org(org)
        return api.get_org_api(org["path"])

    def get_namespace(self, api, namespace):
        return api.get_org_api(namespace)
