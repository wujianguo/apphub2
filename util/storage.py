import os, shutil
from urllib.parse import urlparse
from django.conf import settings
from rest_framework.response import Response

def make_directory(path):
    os.makedirs(path, exist_ok=True)

def remove_directory(path):
    shutil.rmtree(settings.MEDIA_ROOT + '/' + path)

def copy_file(src, dst):
    shutil.copyfile(src, dst)
