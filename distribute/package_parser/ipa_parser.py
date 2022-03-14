#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zipfile, plistlib, re
from application.models import Application
from .base import AppParser

class IpaParser(AppParser):

    @staticmethod
    def can_parse(ext, os=None):
        return ext == 'ipa' and (os == Application.OperatingSystem.iOS or os is None)

    def __init__(self, file):
        self.zip = zipfile.ZipFile(file)
        self.__plist = None

    @property
    def os(self):
        return Application.OperatingSystem.iOS

    @property
    def display_name(self):
        return self.plist.get('CFBundleDisplayName')

    @property
    def bundle_name(self):
        return self.plist.get('CFBundleName')

    @property
    def bundle_identifier(self):
        return self.plist.get('CFBundleIdentifier')

    @property
    def version(self):
        return self.plist.get('CFBundleVersion')

    @property
    def short_version(self):
        return self.plist.get('CFBundleShortVersionString')

    @property
    def minimum_os_version(self):
        return self.plist.get('MinimumOSVersion')

    @property
    def app_icon(self):
        pattern = re.compile(r'Payload/[^/]*.app/AppIcon60x60@3x.png')
        for path in self.zip.namelist():
            m = pattern.match(path)
            if m is not None:
                return self.zip.read(m.group())
        return None

    @property
    def plist(self):
        if self.__plist:
            return self.__plist

        pattern = re.compile(r'Payload/[^/]*.app/Info.plist')
        for path in self.zip.namelist():
            m = pattern.match(path)
            if m is not None:
                # print(m)
                data = self.zip.read(m.group())
                self.__plist = plistlib.loads(data)
        return self.__plist
