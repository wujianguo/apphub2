from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import Http404
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from distribute.serializers import *
from distribute.package_parser import parser
from distribute.models import Release
from application.models import Application, UniversalApp, UniversalAppUser
from util.visibility import VisibilityType


def create_package(request, universal_app):
    serializer = UploadPackageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    file = serializer.validated_data['file']
    ext = file.name.split('.')[-1]
    pkg = parser.parse(file.file, ext)
    if pkg is None:
        raise serializers.ValidationError('Can not parse the package.')
    if pkg.app_icon is not None:
        icon_file = ContentFile(pkg.app_icon)
        icon_file.name = 'icon.png'
    else:
        icon_file = None
    if pkg.os == Application.OperatingSystem.iOS:
        app = universal_app.iOS
    elif pkg.os == Application.OperatingSystem.Android:
        app = universal_app.android
    internal_build = Package.objects.filter(app__universal_app=universal_app).count() + 1
    instance = Package.objects.create(
        app=app,
        name=pkg.display_name,
        package_file=file,
        icon_file=icon_file,
        version=pkg.version,
        short_version=pkg.short_version,
        bundle_identifier=pkg.bundle_identifier,
        internal_build=internal_build,
        min_os=pkg.minimum_os_version,
        extra=pkg.extra,
        size=file.size)
    if not app.icon_file and icon_file is not None:
        app.icon_file = icon_file
        app.save()
    if not universal_app.icon_file and icon_file is not None:
        universal_app.icon_file = icon_file
        universal_app.save()

    serializer = PackageSerializer(instance, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def viewer_query(user, path, ownername):
    if user.is_authenticated:
        allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
        q1 = Q(app__path=path, app__owner__username=ownername)
        q2 = Q(app__visibility__in=allow_visibility)
        q3 = Q(user=user)
        return (q2 | q3) & q1
    else:
        q1 = Q(app__path=path, app__owner__username=ownername)
        q2 = Q(app__visibility=VisibilityType.Public)
        return q1 & q2

def check_app_view_permission(user, path, ownername):
    app_user = UniversalAppUser.objects.filter(viewer_query(user, path, ownername))
    if not app_user.exists():
        raise Http404
    return app_user.first()

def check_app_manager_permission(user, path, ownername):
    try:
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        user_app = UniversalAppUser.objects.get(app__path=path, app__owner__username=ownername, user=user)
        if user_app.role != manager_role:
            raise PermissionDenied
        return user_app
    except UniversalAppUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            UniversalApp.objects.get(path=path, owner__username=ownername, visibility__in=allow_visibility)
            raise PermissionDenied
        except UniversalApp.DoesNotExist:
            raise Http404


class UserAppPackageList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username, path):
        user_app = check_app_view_permission(request.user, path, username)
        packages = Package.objects.filter(app__universal_app=user_app.app)
        serializer = PackageSerializer(packages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        return create_package(request, user_app.app)

class UserAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, universal_app, internal_build):
        try:
            return Package.objects.get(app__universal_app=universal_app, internal_build=internal_build)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, username, path, internal_build):
        user_app = check_app_view_permission(request.user, path, username)
        package = self.get_object(user_app.app, internal_build)
        serializer = PackageSerializer(package, context={'request': request})
        return Response(serializer.data)


class UserAppReleaseList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username, path, environment):
        user_app = check_app_view_permission(request.user, path, username)
        releases = Release.objects.filter(app__universal_app=user_app.app, deployment__name=environment)
        serializer = ReleaseSerializer(releases, many=True)
        return Response(serializer.data)

    def post(self, request, username, path, environment):
        user_app = check_app_manager_permission(request.user, path, username)
        serializer = ReleaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=user_app.app, environment=environment)
        data = ReleaseSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)

class UserAppReleaseDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, universal_app, release_id):
        try:
            return Release.objects.get(app__universal_app=universal_app, release_id=release_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, username, path, release_id):
        user_app = check_app_view_permission(request.user, path, username)
        release = self.get_object(user_app.app, release_id)
        serializer = ReleaseSerializer(release)
        return Response(serializer.data)

class UserStoreAppVivo(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        try:
            store_app = StoreApp.objects.get(app__universal_app=user_app.app)
        except StoreApp.DoesNotExist:
            raise Http404
        serializer = StoreAppSerializer(store_app)
        return Response(serializer.data)

    def post(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        serializer = StoreAppVivoAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=user_app.app)
        data = StoreAppSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)
