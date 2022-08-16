from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

try:
    from system.info import info

    info["time"] = parse_datetime(info["time"])
except:  # noqa: E722
    info = {"time": timezone.now(), "commit_id": ""}


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def info_api(request):
    data = {
        "name": "AppHub",
        "version": "0.1.0",
        "time": timezone.make_aware(timezone.make_naive(info["time"])),
        "commit_id": info["commit_id"],
    }
    return Response(data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def current(request):
    data = {
        "time": timezone.make_aware(timezone.make_naive(timezone.now())),
    }
    return Response(data)
