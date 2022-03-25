from django.conf import settings

def build_absolute_uri(path):
    return settings.EXTERNAL_URL + path
