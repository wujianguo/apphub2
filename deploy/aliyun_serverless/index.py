from apphub.wsgi import application
import os, requests, shutil, oss2

def handler(environ, start_response):
    if os.environ.get('APPHUB_SETTINGS_DEFAULT_SDATABASES_ENGINE', None) == 'django.db.backends.sqlite3':
        access_key_id = os.environ.get('ALIYUN_OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('ALIYUN_OSS_ACCESS_KEY_SECRET')
        end_point = os.environ.get('ALIYUN_OSS_ENDPOINT')
        bucket_name = os.environ.get('ALIYUN_OSS_BUCKET_NAME')
        auth = oss2.AuthV2(access_key_id, access_key_secret)
        endpoint_is_cname = False if end_point.endswith('.aliyuncs.com') else True
        bucket = oss2.Bucket(auth, end_point, bucket_name, is_cname=endpoint_is_cname)
        file = os.environ.get('APPHUB_SETTINGS_DATABASE_NAME', '')

    if os.environ.get('APPHUB_SETTINGS_DEFAULT_SDATABASES_ENGINE', None) == 'django.db.backends.sqlite3':
        if file and not os.path.isfile(file):
            url = bucket.sign_url('GET', 'code/db.sqlite3', 60*60)
            with requests.get(url, stream=True) as r:
                with open(file, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

    ret = application(environ, start_response)

    if os.environ.get('APPHUB_SETTINGS_DEFAULT_SDATABASES_ENGINE', None) == 'django.db.backends.sqlite3' and environ.get('REQUEST_METHOD', '') != 'GET':
        if file and os.path.isfile(file):
            bucket.put_object_from_file('code/db.sqlite3', file)
    return ret
