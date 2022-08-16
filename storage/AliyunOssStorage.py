import json
import os.path
import posixpath
import shutil
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.utils import timezone
from django.utils.deconstruct import deconstructible

try:
    import oss2
    from aliyunsdkcore import client
    from aliyunsdksts.request.v20150401 import AssumeRoleRequest
except:  # noqa: E722
    pass


class AliyunOssFile(File):
    """
    A file returned from Aliyun OSS.
    """

    def __init__(self, file, name, storage):
        super(AliyunOssFile, self).__init__(file, name)
        self._storage = storage

    def open(self, mode="rb"):
        if self.closed:
            self.file = self._storage.open(self.name, mode).file
        return super(AliyunOssFile, self).open(mode)


def _to_posix_path(name):
    return name.replace(os.sep, "/")


@deconstructible
class AliyunOssStorage(Storage):
    def __init__(self):
        self.access_key_id = settings.ALIYUN_OSS_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        self.end_point = settings.ALIYUN_OSS_ENDPOINT
        self.public_url = settings.ALIYUN_OSS_PUBLIC_URL
        self.bucket_name = settings.ALIYUN_OSS_BUCKET_NAME
        self.key_prefix = settings.ALIYUN_OSS_KEY_PREFIX
        self.role_arn = settings.ALIYUN_OSS_ROLE_ARN
        self.region_id = settings.ALIYUN_OSS_REGION_ID
        self.auth = oss2.AuthV2(self.access_key_id, self.access_key_secret)
        endpoint_is_cname = False if self.end_point.endswith(".aliyuncs.com") else True
        self.bucket = oss2.Bucket(
            self.auth, self.end_point, self.bucket_name, is_cname=endpoint_is_cname
        )
        public_url_is_cname = (
            False if self.public_url.endswith(".aliyuncs.com") else True
        )
        self.bucket_url = oss2.Bucket(
            self.auth, self.public_url, self.bucket_name, is_cname=public_url_is_cname
        )
        super().__init__()

    def _get_key_name(self, name):
        if name.startswith("/"):
            name = name[1:]
        return posixpath.normpath(posixpath.join(self.key_prefix, _to_posix_path(name)))

    def _open(self, name, mode="rb"):
        if mode != "rb":
            raise ValueError("OSS files can only be opened in read-only mode")

        target_name = self._get_key_name(name)
        tmpf = tempfile.TemporaryFile()
        obj = self.bucket.get_object(target_name)

        if obj.content_length is None:
            shutil.copyfileobj(obj, tmpf)
        else:
            oss2.utils.copyfileobj_and_verify(
                obj, tmpf, obj.content_length, request_id=obj.request_id
            )
        tmpf.seek(0)
        return AliyunOssFile(tmpf, target_name, self)

    def _save(self, name, content):
        target_name = self._get_key_name(name)
        if isinstance(content, AliyunOssFile):
            self.bucket.copy_object(self.bucket_name, content.name, target_name)
        else:
            content.file.seek(0)
            self.bucket.put_object(target_name, content.file)
        return os.path.normpath(name)

    def delete(self, name):
        self.bucket.delete_object(self._get_key_name(name))

    def exists(self, name):
        name = _to_posix_path(name)
        if name.endswith("/"):
            result = self.bucket.list_objects_v2(prefix=self._get_key_name(name) + "/")
            return len(result.object_list) > 0
        ret = self.bucket.object_exists(self._get_key_name(name))
        if not ret:
            return self.exists(name + "/")
        return ret

    def listdir(self, path):
        path = self._get_key_name(path)
        path = "" if path == "." else path + "/"

        files = []
        dirs = []

        for obj in oss2.ObjectIterator(self.bucket, prefix=path, delimiter="/"):
            if obj.is_prefix():
                dirs.append(obj.key)
            else:
                files.append(obj.key)
        return dirs, files

    def get_file_meta(self, name):
        name = self._get_key_name(name)
        return self.bucket.get_object_meta(name)

    def size(self, name):
        file_meta = self.get_file_meta(name)
        return file_meta.content_length

    def url(self, name):
        name = self._get_key_name(name)
        return self.bucket_url.sign_url("GET", name, 60 * 60 * 24, slash_safe=True)

    def _datetime_from_timestamp(self, ts):
        """
        If timezone support is enabled, make an aware datetime object in UTC;
        otherwise make a naive one in the local timezone.
        """
        tz = timezone.utc if settings.USE_TZ else None
        return datetime.fromtimestamp(ts, tz=tz)

    def get_modified_time(self, name):
        file_meta = self.get_file_meta(name)
        return self._datetime_from_timestamp(file_meta.last_modified)

    get_created_time = get_accessed_time = get_modified_time

    def request_upload(
        self, file_name, description, commit_id, callback_url, slug, uploader
    ):
        key_prefix = self.key_prefix + "temp/upload/" + slug + "/" + uploader + "/"
        resource = "acs:oss:*:*:" + self.bucket_name + "/" + key_prefix + "*"
        policy = {
            "Version": "1",
            "Statement": [
                {"Action": ["oss:PutObject"], "Effect": "Allow", "Resource": [resource]}
            ],
        }
        policy_text = json.dumps(policy).strip()
        clt = client.AcsClient(
            self.access_key_id, self.access_key_secret, self.region_id
        )
        req = AssumeRoleRequest.AssumeRoleRequest()
        req.set_accept_format("json")
        req.set_RoleArn(self.role_arn)
        req.set_RoleSessionName(uploader)
        req.set_DurationSeconds(3600)
        req.set_Policy(policy_text)
        body = clt.do_action_with_exception(req)
        token = json.loads(oss2.to_unicode(body))
        description = description.replace('"', '\\"')
        ret = {
            "callback": {
                "callback_url": callback_url,
                "callback_body": '{"object":${object},"description":"'
                + description
                + '","commit_id":"'
                + commit_id
                + '"}',
                "callback_body_type": "application/json",
            },
            "access_key_id": token["Credentials"]["AccessKeyId"],
            "access_key_secret": token["Credentials"]["AccessKeySecret"],
            "security_token": token["Credentials"]["SecurityToken"],
            "endpoint": self.public_url,
            "is_cname": False if self.public_url.endswith(".aliyuncs.com") else True,
            "bucket": self.bucket_name,
            "key_prefix": key_prefix,
        }
        return ret


@deconstructible
class AliyunOssMediaStorage(AliyunOssStorage):
    pass
