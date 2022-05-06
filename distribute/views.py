from django.core.files.base import ContentFile
from django.http import Http404
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from distribute.serializers import *
from distribute.package_parser import parser
from distribute.models import Release
from application.models import Application
from application.permissions import *
from util.url import get_file_extension
from util.storage import internal_file_response


class UserAppPackageList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission]

    def get_namespace(self, path):
        return Namespace.user(path)

    def package_file_url_name(self):
        return 'user-app-package-file'

    def icon_file_url_name(self):
        return 'user-app-package-icon'

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        packages = Package.objects.filter(app__universal_app=app)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        serializer = PackageSerializer(packages, many=True, context=context)
        return Response(serializer.data)

class OrganizationAppPackageList(UserAppPackageList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def package_file_url_name(self):
        return 'org-app-package-file'

    def icon_file_url_name(self):
        return 'org-app-package-icon'


class UserAppPackageUpload(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission]

    def get_namespace(self, path):
        return Namespace.user(path)

    def url_name(self):
        return 'user-app-package'

    def package_file_url_name(self):
        return 'user-app-package-file'

    def icon_file_url_name(self):
        return 'user-app-package-icon'

    def create_package(self, operator_content_object, data, universal_app):
        serializer = UploadPackageSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        file = serializer.validated_data['file']
        commit_id = serializer.validated_data.get('commit_id', '')
        description = serializer.validated_data.get('description', '')
        ext = get_file_extension(file.name)
        pkg = parser.parse(file.file, ext)
        if pkg is None:
            raise serializers.ValidationError({'message': 'Can not parse the package.'})
        if pkg.app_icon is not None:
            icon_file = ContentFile(pkg.app_icon)
            icon_file.name = 'icon.png'
        else:
            icon_file = None
        app = None
        if pkg.os == Application.OperatingSystem.iOS:
            app = universal_app.iOS
        elif pkg.os == Application.OperatingSystem.Android:
            app = universal_app.android
        if app is None:
            raise serializers.ValidationError({'message': 'OS not supported.'})
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
            commit_id=commit_id,
            description=description,
            extra=pkg.extra,
            size=file.size)
        if not app.icon_file and icon_file is not None:
            app.icon_file = icon_file
            app.save()
        return instance

    def post(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(request.user, path, self.get_namespace(namespace))
            instance = self.create_package(request.user, request.data, app)
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            instance = self.create_package(request.token, request.data, app)

        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        serializer = PackageSerializer(instance, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(self.url_name(), args=(namespace, path, instance.package_id))
        response['Location'] = build_absolute_uri(location)
        return response

class OrganizationAppPackageUpload(UserAppPackageUpload):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def url_name(self):
        return 'org-app-package'

    def package_file_url_name(self):
        return 'org-app-package-file'

    def icon_file_url_name(self):
        return 'org-app-package-icon'


class UserAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def package_file_url_name(self):
        return 'user-app-package-file'

    def icon_file_url_name(self):
        return 'user-app-package-icon'

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(app__universal_app=universal_app, package_id=package_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        serializer = PackageUpdateSerializer(package, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        return Response(PackageSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        # todo: check release, upgrades use
        package.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationAppPackageDetail(UserAppPackageDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def package_file_url_name(self):
        return 'org-app-package-file'

    def icon_file_url_name(self):
        return 'org-app-package-icon'

class UserAppPackageFile(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(app__universal_app=universal_app, package_id=package_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id, name):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        return internal_file_response(package.package_file, name)

class OrganizationAppPackageFile(UserAppPackageFile):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppPackageIcon(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(app__universal_app=universal_app, package_id=package_id)
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id, name):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)
        return internal_file_response(package.icon_file, name)

class OrganizationAppPackageIcon(UserAppPackageIcon):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppReleaseList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def package_file_url_name(self):
        return 'user-app-package-file'

    def icon_file_url_name(self):
        return 'user-app-package-icon'

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        releases = Release.objects.filter(app__universal_app=app)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        serializer = ReleaseSerializer(releases, many=True, context=context)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = ReleaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        data = ReleaseSerializer(instance, context=context).data
        return Response(data, status=status.HTTP_201_CREATED)

class OrganizationAppReleaseList(UserAppReleaseList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def package_file_url_name(self):
        return 'org-app-package-file'

    def icon_file_url_name(self):
        return 'org-app-package-icon'

class UserAppReleaseDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def package_file_url_name(self):
        return 'user-app-package-file'

    def icon_file_url_name(self):
        return 'user-app-package-icon'

    def get_object(self, universal_app, release_id):
        try:
            return Release.objects.get(app__universal_app=universal_app, release_id=release_id)
        except Release.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, release_id):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        release = self.get_object(app, release_id)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        serializer = ReleaseSerializer(release, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        release = self.get_object(app, release_id)
        serializer = ReleaseCreateSerializer(release, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            'package_file_url_name': self.package_file_url_name(),
            'icon_file_url_name': self.icon_file_url_name(),
            'namespace': namespace,
            'path': path
        }
        return Response(ReleaseSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        release = self.get_object(app, release_id)
        if release.enabled:
            release.package.make_internal(app.install_slug)
        # todo: check release, upgrades use
        release.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationAppReleaseDetail(UserAppReleaseDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def package_file_url_name(self):
        return 'org-app-package-file'

    def icon_file_url_name(self):
        return 'org-app-package-icon'

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
