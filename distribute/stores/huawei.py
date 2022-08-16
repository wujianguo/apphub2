import requests

from .base import StoreBase, StoreType


class HuaweiStore(StoreBase):
    def __init__(self, auth_data):
        self.store_url = auth_data.get("store_url", "")

    @staticmethod
    def store_type():
        return StoreType.Huawei

    @staticmethod
    def name():
        return "huawei"

    @staticmethod
    def display_name():
        return "华为"

    def channel(self):
        return "huawei"

    def store_current(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa: E501
        }
        r = requests.get(self.store_url, headers=headers)
        version = r.json()["layoutData"][1]["dataList"][0]["versionName"]
        return {"version": version}
