import logging
import os
import shutil

import oss2
import requests

from apphub.wsgi import application


def handler(environ, start_response):
    logging.info(environ.get("fc.request_uri", ""))
    if (
        os.environ.get("APPHUB_DEFAULT_SDATABASES_ENGINE", None)
        == "django.db.backends.sqlite3"
    ):
        access_key_id = os.environ.get("APPHUB_ALIYUN_OSS_ACCESS_KEY_ID")
        access_key_secret = os.environ.get("APPHUB_ALIYUN_OSS_ACCESS_KEY_SECRET")
        end_point = os.environ.get("APPHUB_ALIYUN_OSS_ENDPOINT")
        bucket_name = os.environ.get("APPHUB_ALIYUN_OSS_BUCKET_NAME")
        auth = oss2.AuthV2(access_key_id, access_key_secret)
        endpoint_is_cname = False if end_point.endswith(".aliyuncs.com") else True
        bucket = oss2.Bucket(auth, end_point, bucket_name, is_cname=endpoint_is_cname)
        file = os.environ.get("APPHUB_DATABASE_NAME", "")
        remote_db_file = file
        if remote_db_file.startswith("/"):
            remote_db_file = remote_db_file[1:]

        if file and not os.path.isfile(file):
            url = bucket.sign_url("GET", remote_db_file, 60 * 60)
            with requests.get(url, stream=True) as r:
                with open(file, "wb") as f:
                    shutil.copyfileobj(r.raw, f)

    ret = application(environ, start_response)

    if (
        os.environ.get("APPHUB_DEFAULT_SDATABASES_ENGINE", None)
        == "django.db.backends.sqlite3"
        and environ.get("REQUEST_METHOD", "") != "GET"
    ):
        if file and os.path.isfile(file):
            bucket.put_object_from_file(remote_db_file, file)
    return ret
