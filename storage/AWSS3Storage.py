import os.path
import random
import string

from django.conf import settings
from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage, S3Boto3StorageFile

from util.url import get_file_extension


class AWSS3MediaStorage(S3Boto3Storage):

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)

        if isinstance(content, S3Boto3StorageFile):
            copy_source = {
                "Bucket": self.bucket.name,
                "Key": os.path.join(self.location, content.name)
            }
            self.bucket.copy(copy_source, name)
            return cleaned_name

        params = self._get_write_parameters(name, content)

        if not hasattr(content, 'seekable') or content.seekable():
            content.seek(0, os.SEEK_SET)
        if (self.gzip and params['ContentType'] in self.gzip_content_types
                and 'ContentEncoding' not in params):
            content = self._compress_content(content)
            params['ContentEncoding'] = 'gzip'

        obj = self.bucket.Object(name)
        obj.upload_fileobj(content, ExtraArgs=params, Config=self._transfer_config)  # noqa: E501
        return cleaned_name

    def request_upload_url(self, slug, filename):
        ext = get_file_extension(filename, "zip")
        name = str(timezone.make_aware(timezone.make_naive(timezone.now())))[:19]  # noqa: E501
        suffix = "".join(random.choices(string.ascii_letters, k=4))
        name = name.replace(' ', 'T').replace(':', '-') + '-' + suffix + '.' + ext  # noqa: E501
        name = os.path.join("temp/upload", slug, name)
        object_name = os.path.join(self.location, name)

        expire_seconds = 60 * 60
        conditions = None
        if settings.AWS_STORAGE_PUBLIC_READ:
            conditions = [{"acl": "public-read"}]

        response = self.bucket.meta.client.generate_presigned_post(
            self.bucket.name,
            object_name,
            Conditions=conditions,
            ExpiresIn=expire_seconds)
        response["file"] = name
        return response
