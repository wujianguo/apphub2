from django.core.files.base import ContentFile
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from distribute.serializers import *
from distribute.package_parser import parser
from distribute.models import Release
from application.models import Application
from application.permissions import *
from util.url import get_file_extension

def create_package(operator_content_object, data, universal_app):
    serializer = UploadPackageSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    file = serializer.validated_data['file']
    ext = get_file_extension(file.name)
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
    package_id = Package.objects.filter(app__universal_app=universal_app).count() + 1
    instance = Package.objects.create(
        operator_object_id=operator_content_object.id,
        operator_content_object=operator_content_object,
        app=app,
        name=pkg.display_name,
        package_file=file,
        icon_file=icon_file,
        version=pkg.version,
        short_version=pkg.short_version,
        bundle_identifier=pkg.bundle_identifier,
        package_id=package_id,
        min_os=pkg.minimum_os_version,
        extra=pkg.extra,
        size=file.size)
    if not app.icon_file and icon_file is not None:
        app.icon_file = icon_file
        app.save()
    serializer = PackageSerializer(instance)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserAppPackageList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        packages = Package.objects.filter(app__universal_app=app)
        serializer = PackageSerializer(packages, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(request.user, path, self.get_namespace(namespace))
            return create_package(request.user, request.data, app)
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return create_package(request.token, request.data, app)            

class OrganizationAppPackageList(UserAppPackageList):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(app__universal_app=universal_app, package_id=package_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        serializer = PackageSerializer(package)
        return Response(serializer.data)

class OrganizationAppPackageDetail(UserAppPackageDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppReleaseList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        releases = Release.objects.filter(app__universal_app=app)
        serializer = ReleaseSerializer(releases, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = ReleaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        data = ReleaseSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)

class OrganizationAppReleaseList(UserAppReleaseList):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppReleaseDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, release_id):
        try:
            return Release.objects.get(app__universal_app=universal_app, release_id=release_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, release_id):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        release = self.get_object(app, release_id)
        serializer = ReleaseSerializer(release)
        return Response(serializer.data)

class OrganizationAppReleaseDetail(UserAppReleaseDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

class UserStoreAppVivo(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        try:
            store_app = StoreApp.objects.get(app__universal_app=app)
        except StoreApp.DoesNotExist:
            raise Http404
        serializer = StoreAppSerializer(store_app)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = StoreAppVivoAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        data = StoreAppSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)

class OrganizationStoreAppVivo(UserStoreAppVivo):
    def get_namespace(self, path):
        return Namespace.organization(path)
