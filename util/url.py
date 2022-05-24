from django.conf import settings

def build_absolute_uri(path):
    if path.startswith('https://') or path.startswith('http://'):
        return path
    if path.startswith('/'):
        return settings.EXTERNAL_API_URL + path
    else:
        return settings.EXTERNAL_API_URL + '/' + path

def get_file_extension(filename, default='png'):
    ext = default
    items = filename.split('.')
    if len(items) > 1 and items[-1].isalpha():
        ext = items[-1]
    return ext
