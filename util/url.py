from django.conf import settings

def build_absolute_uri(path):
    return settings.EXTERNAL_URL + path

def get_file_extension(filename, default='png'):
    ext = default
    items = filename.split('.')
    if len(items) > 1 and items[-1].isalpha():
        ext = items[-1]
    return ext
