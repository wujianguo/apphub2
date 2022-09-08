import requests

from .base import StoreBase, StoreType


class YingyongbaoStore(StoreBase):
    def __init__(self, auth_data):
        self.bundle_identifier = auth_data.get("bundle_identifier", "")

    @staticmethod
    def store_type():
        return StoreType.Yingyongbao

    @staticmethod
    def name():
        return "yingyongbao"

    @staticmethod
    def display_name():
        return "应用宝"

    def channel(self):
        return "yingyongbao"

    def store_current(self):
        version = ""
        url = (
            "https://a.app.qq.com/o/simple.jsp?pkgname="
            + self.bundle_identifier
            + "&g_f=1000047"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa: E501
        }
        r = requests.get(url, headers=headers)
        start = r.text.find("版本")
        if start != -1:
            sub = r.text[start + 3 : start + 20]
            end = sub.find("\n")
            version = sub[:end]
        return {"version": version}
