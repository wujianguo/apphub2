#!/usr/bin/env python
# -*- coding: utf-8 -*-

from androguard.core.bytecodes.apk import APK

from application.models import Application

from .base import AppParser


class ApkParser(AppParser):
    @staticmethod
    def can_parse(ext, os=None, platform=None):
        return ext == "apk" and (
            os == Application.OperatingSystem.Android or os is None
        )

    def __init__(self, file):
        self.apk = APK(file.read(), raw=True)

    @property
    def os(self):
        return Application.OperatingSystem.Android

    @property
    def display_name(self):
        return self.apk.get_app_name()

    @property
    def version(self):
        return self.apk.get_androidversion_code()

    @property
    def short_version(self):
        return self.apk.get_androidversion_name()

    @property
    def minimum_os_version(self):
        sdk_version_dict = {
            "11": "3.0.x",
            "12": "3.1.x",
            "13": "3.2",
            "14": "4.0, 4.0.1, 4.0.2",
            "15": "4.0.3, 4.0.4",
            "16": "4.1, 4.1.1",
            "17": "4.2, 4.2.2",
            "18": "4.3",
            "19": "4.4",
            "20": "4.4W",
            "21": "5.0",
            "22": "5.1",
            "23": "6.0",
            "24": "7.0",
            "25": "7.1, 7.1.1",
            "26": "8.0",
            "27": "8.1",
            "28": "9",
            "29": "10.0",
        }
        return sdk_version_dict.get(self.apk.get_min_sdk_version(), "")

    @property
    def bundle_identifier(self):
        return self.apk.get_package()

    @property
    def app_icon(self):
        return self.apk.get_file(self.apk.get_app_icon())

    @property
    def extra(self):
        return {
            "min_sdk_version": self.apk.get_min_sdk_version(),
            "target_sdk_version": self.apk.get_target_sdk_version(),
        }
