from client.client import BaseClient
from util.image import generate_random_image


class Api:
    class UserApi:
        def __init__(self, client: BaseClient, username=""):
            self.username = username
            if not self.username:
                self.username = client.username
            self.client = client

        def set_username(self, username):
            self.username = username

        def force_login_or_register(self, username):
            self.client.login_or_create(username)
            self.username = username
            self.client.set_username(username)

        def register(self, user):
            return self.client.post("/user/register", user)

        def confirm_register(self, code):
            return self.client.post("/user/register/verify_email", {"key": code})

        def login(self, user):
            r = self.client.post("/user/login", user)
            if r.status_code == 200:
                self.username = r.json()["username"]
                self.client.set_username(self.username)
                self.client.set_token(r.json()["token"])
            return r

        def logout(self):
            return self.client.delete("/user/logout")

        def me(self):
            return self.client.get("/user")

        def update(self, user):
            return self.client.put("/user", user)

        def update_avatar(self, avatar_file_path=None):
            if avatar_file_path is None:
                file = generate_random_image()
                file_path = file.name
            else:
                file_path = avatar_file_path

            with open(file_path, "rb") as fp:
                data = {"avatar": fp}
                return self.client.upload_post("/user/avatar", data=data)

        def change_password(self, password, new_password):
            payload = {
                "old_password": password,
                "new_password1": new_password,
                "new_password2": new_password,
            }
            return self.client.post("/user/password/change", payload)

        def request_reset_password(self, email):
            payload = {"email": email}
            return self.client.post("/user/password/reset", payload)

        def reset_password(self, username, token, password):
            payload = {
                "username": username,
                "token": token,
                "new_password1": password,
                "new_password2": password,
            }
            return self.client.post("/user/password/reset/confirm", payload)

        def request_verify_email(self):
            return self.client.post("/user/email/request_verify")

        def resend_register_email(self, email):
            payload = {"email": email}
            return self.client.post("/user/register/resend_email", payload)

        def verify_register_email(self, code):
            payload = {"key": code}
            return self.client.post("/user/register/verify_email", payload)

        def get_user(self, username):
            return self.client.get("/users/" + username)

        def create_org(self, org):
            return self.client.post("/orgs", org)

        def get_org_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get("/" + self.username + "/orgs", query)

        def get_my_app_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get("/user/apps", query)

        def get_app_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get("/users/" + self.username + "/apps", query)

        def get_visible_org_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get("/orgs", query)

        def get_app_api(self, path):
            return Api.UniversalAppApi(self.client, path, self.username)

        def create_app(self, app):
            return self.client.post("/user/apps", app)

        def get_visible_app_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get("/apps", query)

    class OrganizationApi:
        def __init__(self, client, path):
            self.client = client
            self.base_path = "/orgs/" + path
            self.path = path

        def get_org(self):
            return self.client.get(self.base_path)

        def update_org(self, org):
            return self.client.put(self.base_path, org)

        def remove_org(self):
            return self.client.delete(self.base_path)

        def change_or_set_icon(self, icon_file_path=None):
            if icon_file_path is None:
                file = generate_random_image()
                file_path = file.name
            else:
                file_path = icon_file_path

            with open(file_path, "rb") as fp:
                data = {"icon_file": fp}
                return self.client.upload_post(self.base_path + "/icons", data=data)

        # def get_icon(self):
        #     return self.client.get(self.base_path + '/icon')

        # def remove_icon(self):
        #     return self.client.delete(self.base_path + '/icon')

        def add_member(self, username, role):
            collaborator = {"username": username, "role": role}
            return self.client.post(self.base_path + "/members", collaborator)

        def get_member(self, username):
            return self.client.get(self.base_path + "/members/" + username)

        def get_member_list(self):
            return self.client.get(self.base_path + "/members")

        def change_member_role(self, username, role):
            data = {"role": role}
            return self.client.put(self.base_path + "/members/" + username, data)

        def remove_member(self, username):
            return self.client.delete(self.base_path + "/members/" + username)

        def create_app(self, app):
            return self.client.post(self.base_path + "/apps", app)

        def get_app_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get(self.base_path + "/apps", query)

        def get_app_api(self, path):
            return Api.UniversalAppApi(self.client, path, org=self.path)

    class UniversalAppApi:
        def __init__(self, client, path, owner="", org=""):
            self.client = client
            if owner:
                self.base_path = "/users/" + owner + "/apps/" + path
            if org:
                self.base_path = "/orgs/" + org + "/apps/" + path

        def get_app(self):
            return self.client.get(self.base_path)

        def update_app(self, app):
            return self.client.put(self.base_path, app)

        def remove_app(self):
            return self.client.delete(self.base_path)

        def change_or_set_icon(self, icon_file_path=None):
            if icon_file_path is None:
                file = generate_random_image()
                file_path = file.name
            else:
                file_path = icon_file_path

            with open(file_path, "rb") as fp:
                data = {"icon_file": fp}
                return self.client.upload_post(self.base_path + "/icons", data=data)

        # def get_icon(self, name):
        #     return self.client.get(self.base_path + '/icons/' + name)

        # def remove_icon(self):
        #     return self.client.delete(self.base_path + '/icon')

        def add_member(self, username, role):
            collaborator = {"username": username, "role": role}
            return self.client.post(self.base_path + "/members", collaborator)

        def get_member(self, username):
            return self.client.get(self.base_path + "/members/" + username)

        def get_member_list(self):
            return self.client.get(self.base_path + "/members")

        def change_member_role(self, username, role):
            data = {"role": role}
            return self.client.put(self.base_path + "/members/" + username, data)

        def remove_member(self, username):
            return self.client.delete(self.base_path + "/members/" + username)

        def upload_package(self, file_path):
            with open(file_path, "rb") as fp:
                data = {"file": fp}
                url = self.base_path + "/packages/upload_via_file"
                return self.client.upload_post(url, data=data)

        def get_package_list(self, page=1, per_page=10):
            query = {"page": page, "per_page": per_page}
            return self.client.get(self.base_path + "/packages", query)

        def get_one_package(self, package_id):
            return self.client.get(self.base_path + "/packages/" + str(package_id))

        def update_package(self, package_id, data):
            return self.client.put(
                self.base_path + "/packages/" + str(package_id), data
            )

        def remove_package(self, package_id):
            return self.client.delete(self.base_path + "/packages/" + str(package_id))

        def create_release(self, release):
            return self.client.post(self.base_path + "/releases", release)

        def get_release_list(self):
            return self.client.get(self.base_path + "/releases")

        def get_one_release(self, release_id):
            return self.client.get(self.base_path + "/releases/" + str(release_id))

        def update_release(self, release_id, data):
            return self.client.put(
                self.base_path + "/releases/" + str(release_id), data
            )

        def remove_release(self, release_id):
            return self.client.delete(self.base_path + "/releases/" + str(release_id))

        def create_token(self, data):
            return self.client.post(self.base_path + "/tokens", data)

        def get_token_list(self):
            return self.client.get(self.base_path + "/tokens")

        def get_one_token(self, token_id):
            return self.client.get(self.base_path + "/tokens/" + str(token_id))

        def update_token(self, token_id, data):
            return self.client.put(self.base_path + "/tokens/" + str(token_id), data)

        def remove_token(self, token_id):
            return self.client.delete(self.base_path + "/tokens/" + str(token_id))

        def create_webhook(self, data):
            return self.client.post(self.base_path + "/webhooks", data)

        def get_webhook_list(self):
            return self.client.get(self.base_path + "/webhooks")

        def get_one_webhook(self, webhook_id):
            return self.client.get(self.base_path + "/webhooks/" + str(webhook_id))

        def update_webhook(self, webhook_id, data):
            return self.client.put(
                self.base_path + "/webhooks/" + str(webhook_id), data
            )

        def remove_webhook(self, webhook_id):
            return self.client.delete(self.base_path + "/webhooks/" + str(webhook_id))

        def get_stores(self):
            return self.client.get(self.base_path + "/stores")

        def create_appstore(self, appstore_app_id, country_code_alpha2):
            data = {
                "appstore_app_id": appstore_app_id,
                "country_code_alpha2": country_code_alpha2
            }
            return self.client.post(self.base_path + "/stores/appstore", data)

        def get_appstore_auth(self):
            return self.client.get(self.base_path + "/stores/appstore")

        def create_huawei_store(self, store_url, store_link):
            data = {
                "store_url": store_url,
                "store_link": store_link
            }
            return self.client.post(self.base_path + "/stores/huawei", data)

        def get_huawei_auth(self):
            return self.client.get(self.base_path + "/stores/huawei")

        def create_vivo_store(self, vivo_store_app_id):
            data = {
                "vivo_store_app_id": vivo_store_app_id
            }
            return self.client.post(self.base_path + "/stores/vivo", data)

        def get_vivo_auth(self):
            return self.client.get(self.base_path + "/stores/vivo")

        def create_xiaomi_store(self, xiaomi_store_app_id):
            data = {
                "xiaomi_store_app_id": xiaomi_store_app_id
            }
            return self.client.post(self.base_path + "/stores/xiaomi", data)

        def get_xiaomi_auth(self):
            return self.client.get(self.base_path + "/stores/xiaomi")

        def create_yingyongbao_store(self, bundle_identifier):
            data = {
                "bundle_identifier": bundle_identifier
            }
            return self.client.post(self.base_path + "/stores/yingyongbao", data)

        def get_yingyongbao_auth(self):
            return self.client.get(self.base_path + "/stores/yingyongbao")

        def update_stores_versions(self):
            return self.client.post(self.base_path + "/stores/current/versions")

        def get_stores_versions(self):
            return self.client.get(self.base_path + "/stores/current/versions")

        def submit_store(self, release_id, release_notes, store):
            payload = {
                "release_id": release_id,
                "release_notes": release_notes,
                "store": store,
            }
            return self.client.post(self.base_path + "/stores/submit", payload)

    def __init__(self, client, username="", auto_login=False):
        self.client = client
        if username and auto_login:
            self.get_user_api().force_login_or_register(username)

    def get_user_api(self, username=""):
        return Api.UserApi(self.client, username)

    def get_org_api(self, path):
        return Api.OrganizationApi(self.client, path)

    def get_or_head_file(self, path):
        return self.client.get_or_head_file(path)

    def get(self, path):
        return self.client.get(path)

    def get_swagger(self):
        return self.client.get("/docs/swagger.json")

    def upload_package(self, file_path, token):
        with open(file_path, "rb") as fp:
            data = {"file": fp}
            url = "/upload/file"
            return self.client.upload_post(url, data=data, token=token)

    def get_appstore_app_version(self, appstore_app_id, country_code_alpha2):
        return self.client.get(
            "/stores/appstore/" + country_code_alpha2 + "/" + appstore_app_id
        )

    def get_huawei_app_version(self, store_url):
        query = {"store_url": store_url}
        return self.client.get("/stores/huawei", query)

    def get_vivo_app_version(self, vivo_store_app_id):
        return self.client.get("/stores/vivo/" + str(vivo_store_app_id))

    def get_xiaomi_app_version(self, xiaomi_store_app_id):
        return self.client.get("/stores/xiaomi/" + str(xiaomi_store_app_id))

    def get_yingyongbao_app_version(self, bundle_identifier):
        query = {"bundle_identifier": bundle_identifier}
        return self.client.get("/stores/yingyongbao", query)
