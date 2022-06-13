from django.conf import settings

def build_absolute_uri(path):
    if path.startswith('https://') or path.startswith('http://'):
        return path
    if path.startswith('/' + settings.API_URL_PREFIX):
        path = path[len(settings.API_URL_PREFIX)+1:]
    if path and path[0] != '/' and settings.EXTERNAL_API_URL and settings.EXTERNAL_API_URL[-1] != '/':
        return settings.EXTERNAL_API_URL + '/' + path
    return settings.EXTERNAL_API_URL + path

def get_file_extension(filename, default='png'):
    ext = default
    items = filename.split('.')
    if len(items) > 1 and items[-1].isalpha():
        ext = items[-1]
    return ext
