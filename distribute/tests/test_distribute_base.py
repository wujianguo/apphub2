import os
import shutil

import requests
from django.conf import settings

from util.tests import BaseTestCase


class DistributeBaseTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        package_dir = os.path.join(settings.STATIC_ROOT, "downloads")

        if not os.path.exists(package_dir):
            os.makedirs(package_dir)
        self.apk_path = os.path.join(package_dir, "android-sample.apk")
        if not os.path.exists(self.apk_path):
            url = "https://raw.githubusercontent.com/bitbar/test-samples/master/apps/android/bitbar-sample-app.apk"  # noqa: E501
            with requests.get(url, stream=True) as r:
                with open(self.apk_path, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
        self.ipa_path = os.path.join(package_dir, "ios-sample.ipa")
        if not os.path.exists(self.ipa_path):
            url = "https://raw.githubusercontent.com/bitbar/test-samples/master/apps/ios/bitbar-ios-sample.ipa"  # noqa: E501
            with requests.get(url, stream=True) as r:
                with open(self.ipa_path, "wb") as f:
                    shutil.copyfileobj(r.raw, f)

        self.apk1_path = os.path.join(package_dir, "android-sample-25.apk")
        self.apk2_apth = os.path.join(package_dir, "android-sample-26.apk")
        self.apk3_apth = os.path.join(package_dir, "android-sample-28.apk")
        self.apk4_apth = os.path.join(package_dir, "android-sample-30.apk")
