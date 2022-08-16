import requests

from .base import StoreBase, StoreType


class AppStore(StoreBase):
    def __init__(self, auth_data):
        self.country_code_alpha2 = auth_data["country_code_alpha2"].lower()
        self.appstore_app_id = auth_data["appstore_app_id"]
        self.app_name = auth_data.get("app_name", "default")
        self.key_word = auth_data.get("key_word", "Version ")  # ">版本
        self.key_word_list = [">Version ", ">版本 "]

    @staticmethod
    def store_type():
        return StoreType.AppStore

    @staticmethod
    def name():
        return "appstore"

    @staticmethod
    def display_name():
        return "AppStore"

    def channel(self):
        return "appstore"

    def store_current(self):
        version = ""
        url = (
            "https://apps.apple.com/"
            + self.country_code_alpha2
            + "/app/"
            + self.app_name
            + "/id"
            + self.appstore_app_id
        )
        r = requests.get(url)
        key_word = self.key_word
        start = r.text.find(key_word)
        if start == -1:
            for item in self.key_word_list:
                start = r.text.find(item)
                if start != -1:
                    key_word = item
                    break
        if start != -1:
            sub = r.text[start + len(key_word) : start + 20]
            end = sub.find("</p>")
            version = sub[:end]
        return {"version": version}
