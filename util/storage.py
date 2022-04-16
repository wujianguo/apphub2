import os
from urllib.parse import urlparse
from django.conf import settings
from rest_framework.response import Response

def make_file_public(model, file):
    if file.name.startswith('public/'):
        return
    initial_path = settings.MEDIA_ROOT + '/' + file.name
    file.name = file.name.replace('internal', 'public')
    new_path = settings.MEDIA_ROOT + '/' + file.name
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    os.rename(initial_path, new_path)
    model.save()

def internal_file_response(file, name):
    response = Response()
    redirect = urlparse(settings.MEDIA_URL).path + os.path.join(os.path.dirname(file.name), name)
    response['X-Accel-Redirect'] = redirect
    response['Content-Type'] = ''
    return response
