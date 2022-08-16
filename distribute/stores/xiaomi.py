import requests

from .base import StoreBase, StoreType


class XiaomiStore(StoreBase):
    def __init__(self, auth_data):
        self.xiaomi_store_app_id = auth_data.get("xiaomi_store_app_id", "")

    @staticmethod
    def store_type():
        return StoreType.Xiaomi

    @staticmethod
    def name():
        return "xiaomi"

    @staticmethod
    def display_name():
        return "小米"

    def channel(self):
        return "xiaomi"

    def store_current(self):
        url = "https://m.app.mi.com/detailapi/" + str(self.xiaomi_store_app_id)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa: E501
        }
        r = requests.get(url, headers=headers)
        version = r.json()["appMap"]["versionName"]
        return {"version": version}
