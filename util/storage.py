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

def internal_file_response(file, name):
    response = Response()
    redirect = urlparse(settings.MEDIA_URL).path + os.path.join(os.path.dirname(file.name), name)
    response['X-Accel-Redirect'] = redirect
    response['Content-Type'] = ''
    return response
