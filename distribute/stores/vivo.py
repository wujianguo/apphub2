import hashlib
import hmac
import time

import requests
from django.conf import settings

from .base import StoreBase, StoreType


class VivoStore(StoreBase):
    def __init__(self, auth_data):
        self.access_key = auth_data.get("access_key", "")
        self.access_secret = auth_data.get("access_secret", "")
        self.vivo_store_app_id = auth_data.get("vivo_store_app_id", "")

    @staticmethod
    def store_type():
        return StoreType.Vivo

    @staticmethod
    def name():
        return "vivo"

    @staticmethod
    def display_name():
        return "Vivo"

    @staticmethod
    def icon():
        return settings.STATIC_URL + "store/vivo.png"

    def channel(self):
        return "vivo"

    def _request(self, payload):
        timestamp = int(time.time() * 1000)
        request_payload = {
            "access_key": self.access_key,
            "timestamp": timestamp,
            "format": "json",
            "v": "1.0",
            "sign_method": "hmac",
            "target_app_key": "developer",
        }
        request_payload.update(payload)
        message = "&".join(
            list(k + "=" + str(request_payload[k]) for k in sorted(request_payload))
        ).encode("utf-8")
        sign = hmac.new(
            bytes(self.access_secret, "latin-1"), msg=message, digestmod=hashlib.sha256
        )
        request_payload["sign"] = sign.hexdigest()
        url = "https://developer-api.vivo.com.cn/router/rest"
        r = requests.post(url, data=request_payload)
        return r.json()

    def submit(self, package):
        payload = {
            "method": "app.update.app",
            "packageName": package.bundle_identifier,
            "apkUrl": package.package_download_url,
            "versionCode": package.version,
            "apkMd5": package.fingerprint,
            "onlineType": 1,
            "updateDesc": package.release_notes,
        }
        r = self._request(payload)
        if r.json()["code"] == 0 and r.json()["subCode"] == 0:
            return {"error": {"code": "success", "message": "success"}}
        return {"error": {"code": "failure", "message": r.json()["msg"]}}

    def submit_result(self, submit_id):
        bundle_identifier = submit_id
        payload = {
            "method": "app.query.task.status",
            "packageName": bundle_identifier,
            "packetType": 0,
        }
        r = self._request(payload)
        if r.json()["code"] == 0 and r.json()["data"]["status"] == 3:
            return {"error": {"code": "success"}}
        return {"error": {"code": "failure", "message": r.json()["msg"]}}

    def store_current(self):
        url = "https://h5-api.appstore.vivo.com.cn/detailInfo"
        payload = {
            "appId": self.vivo_store_app_id,
            "imei": "1234567890",
            "av": "18",
            "app_version": "2100",
            "pictype": "webp",
            "h5_websource": "h5appstore",
            "frompage": "messageh5",
        }
        r = requests.post(url, payload)
        version = r.json()["version_name"]
        return {"version": version}


class MockVivoStore(VivoStore):
    def submit(self, package):
        pass

    def submit_result(self, submit_id):
        pass

    def current_version(self):
        return "1.0.0"


# {'code': 0, 'msg': '应用更新数据提交成功，请稍后查询结果', 'subCode': '0', 'timestamp': 1644913822356}
# {'code': 0, 'msg': '更新版本比上架版本低，更新失败', 'subCode': '12008', 'timestamp': 1645153192647}

# {'code': 0, 'data': {'packageName': 'top.libms.app.apphub', 'status': 1, 'errorReason': '', 'packetType': 0}, 'msg': 'success', 'subCode': '0', 'timestamp': 1644913835799} # noqa: E501
# {'code': 0, 'data': {'packageName': 'top.libms.app.apphub', 'status': 3, 'errorReason': '', 'packetType': 0}, 'msg': 'success', 'subCode': '0', 'timestamp': 1644913869475} # noqa: E501
# {'code': 0, 'data': {'packageName': 'top.libms.app.apphub', 'status': 4, 'errorReason': '文件地址不合法，无法进行下载', 'packetType': 0}, 'msg': 'success', 'subCode': '0', 'timestamp': 1645153147163} # noqa: E501
