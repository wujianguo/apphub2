import os.path
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.signing import BadSignature, TimestampSigner
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@deconstructible
class NginxPublicFileStorage(FileSystemStorage):
    def __init__(self):
        location = os.path.join(settings.MEDIA_ROOT, "public")
        super().__init__(location)


@deconstructible
class NginxPrivateFileStorage(FileSystemStorage):
    def __init__(self):
        location = os.path.join(settings.MEDIA_ROOT, "internal")
        super().__init__(location)

    def url(self, name):
        signer = TimestampSigner()
        value = signer.sign(name)
        value = ":".join(value.split(":")[1:])
        location = reverse("file", args=(name,))
        return self.build_absolute_uri(location) + "?sign=" + value

    def build_absolute_uri(self, location):
        # todo
        if location.startswith("/" + settings.API_URL_PREFIX):
            location = location[len(settings.API_URL_PREFIX) + 1 :]
        if not settings.EXTERNAL_API_URL:
            return "/" + location
        return settings.EXTERNAL_API_URL + location


@api_view(["HEAD", "GET"])
@permission_classes([permissions.AllowAny])
def nginx_media(request, file):
    sign = request.GET.get("sign", "")
    signer = TimestampSigner()
    try:
        value = signer.unsign(
            file + ":" + sign, max_age=timedelta(seconds=60 * 60 * 24)
        )
    except BadSignature:
        raise PermissionDenied

    if value != file:
        raise PermissionDenied
    response = Response()
    redirect = urlparse(settings.MEDIA_URL).path + "internal/" + file
    response["X-Accel-Redirect"] = redirect
    response["Content-Type"] = ""
    return response
