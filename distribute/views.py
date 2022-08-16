from datetime import timedelta
from urllib.parse import unquote

from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.signing import BadSignature, TimestampSigner
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.models import AppAPIToken, Application
from application.permissions import (Namespace, UploadPackagePermission,
                                     check_app_download_permission,
                                     check_app_manager_permission,
                                     check_app_upload_permission,
                                     check_app_view_permission, get_app,
                                     get_slug_app)
from application.serializers import UniversalAppSerializer
from application.views import UserModel
from distribute.models import Package, Release, StoreApp
from distribute.package_parser import parser
from distribute.serializers import (PackageSerializer, PackageUpdateSerializer,
                                    ReleaseCreateSerializer, ReleaseSerializer,
                                    RequestUploadPackageSerializer,
                                    StoreAppSerializer,
                                    StoreAppVivoAuthSerializer,
                                    UploadAliyunOssPackageSerializer,
                                    UploadPackageSerializer)
from distribute.stores.app_store import AppStore
from distribute.stores.huawei import HuaweiStore
from distribute.stores.vivo import VivoStore
from distribute.stores.xiaomi import XiaomiStore
from distribute.stores.yingyongbao import YingyongbaoStore
from util.choice import ChoiceField
from util.pagination import get_pagination_params
from util.url import build_absolute_uri, get_file_extension


class SlugAppDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, slug):
        app = check_app_download_permission(request.user, slug)
        data = UniversalAppSerializer(app).data
        return Response(data)


class SlugAppPackageList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, slug):
        app = check_app_download_permission(request.user, slug)
        page, per_page = get_pagination_params(request)
        os = request.GET.get("os", None)

        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path

        if os:
            query = Package.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Package.objects.filter(app__universal_app=app)
        count = query.count()
        packages = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(packages, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)


class SlugAppPackageLatest(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, slug):
        app = check_app_download_permission(request.user, slug)
        tryOS = request.GET.get("tryOS", None)
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path

        if tryOS and tryOS in app.enable_os_enum_list():
            package = (
                Package.objects.filter(
                    app__universal_app=app,
                    app__os=ChoiceField(
                        choices=Application.OperatingSystem.choices
                    ).to_internal_value(tryOS),
                )
                .order_by("-create_time")
                .first()
            )
        else:
            package = (
                Package.objects.filter(app__universal_app=app)
                .order_by("-create_time")
                .first()
            )
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)


class SlugAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, slug, package_id):
        app = check_app_download_permission(request.user, slug)
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path
        package = self.get_object(app, package_id)
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)


class UserAppPackageList(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission
    ]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        os = request.GET.get("os", None)
        page, per_page = get_pagination_params(request)

        if os:
            query = Package.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Package.objects.filter(app__universal_app=app)
        count = query.count()
        packages = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]

        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(packages, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)


class OrganizationAppPackageList(UserAppPackageList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppPackageUpload(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def url_name(self):
        return "user-app-package"

    def plist_url_name(self):
        return "user-app-package-plist"

    def create_package(
        self,
        operator_content_object,
        universal_app,
        file,
        commit_id="",
        description="",
        build_type="Debug",
    ):
        ext = get_file_extension(file.name)
        pkg = parser.parse(file.file, ext)
        if pkg is None:
            raise serializers.ValidationError({"message": "Can not parse the package."})
        if pkg.app_icon is not None:
            icon_file = ContentFile(pkg.app_icon)
            icon_file.name = "icon.png"
        else:
            icon_file = None
        app = None
        if pkg.os == Application.OperatingSystem.iOS:
            app = universal_app.iOS
        elif pkg.os == Application.OperatingSystem.Android:
            app = universal_app.android
        if app is None:
            raise serializers.ValidationError({"message": "OS not supported."})
        package_id = (
            Package.objects.filter(app__universal_app=universal_app).count() + 1
        )
        instance = Package.objects.create(
            operator_object_id=operator_content_object.id,
            operator_content_object=operator_content_object,
            build_type=build_type,
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
            size=file.size,
        )
        if not app.icon_file and icon_file is not None:
            app.icon_file = icon_file
            app.save()
        return instance

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def post(self, request, namespace, path):
        serializer = UploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        file = serializer.validated_data["file"]
        commit_id = serializer.validated_data.get("commit_id", "")
        description = serializer.validated_data.get("description", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        app = self.check_and_get_app(request, namespace, path)
        instance = self.create_package(
            request.user, app, file, commit_id, description, build_type
        )

        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(instance, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(self.url_name(), args=(namespace, path, instance.package_id))
        response["Location"] = build_absolute_uri(location)
        return response


class OrganizationAppPackageUpload(UserAppPackageUpload):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def url_name(self):
        return "org-app-package"

    def plist_url_name(self):
        return "org-app-package-plist"


class TokenAppPackageUpload(UserAppPackageUpload):

    permission_classes = [UploadPackagePermission]

    def get_namespace(self, app):
        if app.owner:
            return Namespace.user(app.owner.username)
        elif app.org:
            return Namespace.organization(app.org.path)
        else:
            return None

    def url_name(self, app):
        if app.owner:
            return "user-app-package"
        elif app.org:
            return "org-app-package"
        return ""

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"
        return ""

    def post(self, request):
        serializer = UploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        app = request.token.app
        file = serializer.validated_data["file"]
        commit_id = serializer.validated_data.get("commit_id", "")
        description = serializer.validated_data.get("description", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        instance = self.create_package(
            request.token, app, file, commit_id, description, build_type
        )

        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": self.get_namespace(app).path,
            "path": app.path,
        }
        serializer = PackageSerializer(instance, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(
            self.url_name(app),
            args=(self.get_namespace(app).path, app.path, instance.package_id),
        )
        response["Location"] = build_absolute_uri(location)
        return response


class AliyunOssUploadPackageCallback(UserAppPackageUpload):
    permission_classes = [permissions.AllowAny]

    def url_name(self):
        if self.app.owner:
            return "user-app-package"
        elif self.app.org:
            return "org-app-package"
        else:
            return ""

    def plist_url_name(self):
        if self.app.owner:
            return "user-app-package-plist"
        elif self.app.org:
            return "org-app-package-plist"
        else:
            return ""

    def get_uploader(self, type, uploader, app=None):
        if type == "user":
            return UserModel.objects.get(username=uploader)
        elif type == "token":
            # todo: more than one AppAPIToken have the same name and app
            return AppAPIToken.objects.get(name=uploader, app=app)
        else:
            raise PermissionDenied

    def post(self, request, uploader_type, uploader_name, slug):
        # todo
        serializer = UploadAliyunOssPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        app = get_slug_app(slug)
        self.app = app
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path
        path = app.path

        file = default_storage.open(serializer.validated_data["object"])
        commit_id = serializer.validated_data.get("commit_id", "")
        description = serializer.validated_data.get("description", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        uploader = self.get_uploader(uploader_type, uploader_name, app)
        instance = self.create_package(
            uploader, app, file, commit_id, description, build_type
        )

        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(instance, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(self.url_name(), args=(namespace, path, instance.package_id))
        response["Location"] = build_absolute_uri(location)
        return response


class AliyunOssRequestUploadPackage(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission
    ]

    def get_namespace(self, app, namespace):
        if app.owner:
            return Namespace.user(namespace)
        elif app.org:
            return Namespace.organization(namespace)
        else:
            return None

    def check_app(self, request, app):
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path
        path = app.path

        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(app, namespace)
            )
            return app
        else:
            self.check_object_permissions(request, app)
            return app

    def post(self, request, slug):
        serializer = RequestUploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        file_name = serializer.validated_data["file_name"]
        description = serializer.validated_data.get("description", "")
        commit_id = serializer.validated_data.get("commit_id", "")
        app = get_slug_app(slug)
        self.check_app(request, app)
        uploader_type = ""
        uploader_name = ""
        if request.user.is_authenticated:
            uploader_type = "user"
            uploader_name = request.user.username
        elif request.token:
            uploader_type = "token"
            uploader_name = request.token.name
        response = Response()
        location = reverse(
            "aliyun-oss-callback", args=(uploader_type, uploader_name, slug)
        )
        callback_url = build_absolute_uri(location)
        response.data = default_storage.request_upload(
            file_name, description, commit_id, callback_url, slug, uploader_name
        )
        return response


class UserAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        serializer = PackageUpdateSerializer(package, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        return Response(PackageSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        # todo: check release, upgrades use
        package.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationAppPackageDetail(UserAppPackageDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppPackagePlist(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    template_name = "install.plist"

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, sign_name, sign_value, package_id):
        name = namespace + path + str(package_id)
        sign = sign_name + ":" + sign_value
        signer = TimestampSigner()
        try:
            value = signer.unsign(
                name + ":" + sign, max_age=timedelta(seconds=60 * 60 * 24)
            )
        except BadSignature:
            raise PermissionDenied

        if value != name:
            raise PermissionDenied

        app = get_app(path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)

        data = {
            "ipa": package.package_file.url,
            "icon": package.icon_file.url,
            "identifier": package.bundle_identifier,
            "version": package.short_version,
            "name": package.name,
        }
        return render(request, self.template_name, data, content_type="application/xml")


class OrganizationAppPackagePlist(UserAppPackagePlist):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserAppReleaseList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        os = request.GET.get("os", None)
        page, per_page = get_pagination_params(request)

        if os:
            query = Release.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Release.objects.filter(app__universal_app=app)
        count = query.count()
        releases = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = ReleaseSerializer(releases, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        serializer = ReleaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        data = ReleaseSerializer(instance, context=context).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationAppReleaseList(UserAppReleaseList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppReleaseDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get_object(self, universal_app, release_id):
        try:
            return Release.objects.get(
                app__universal_app=universal_app, release_id=release_id
            )
        except Release.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, release_id):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = ReleaseSerializer(release, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        serializer = ReleaseCreateSerializer(release, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        return Response(ReleaseSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        if release.enabled:
            release.package.make_internal(app.install_slug)
        # todo: check release, upgrades use
        release.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationAppReleaseDetail(UserAppReleaseDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserStoreAppVivo(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        try:
            store_app = StoreApp.objects.get(app__universal_app=app)
        except StoreApp.DoesNotExist:
            raise Http404
        serializer = StoreAppSerializer(store_app)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        serializer = StoreAppVivoAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        data = StoreAppSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationStoreAppVivo(UserStoreAppVivo):
    def get_namespace(self, path):
        return Namespace.organization(path)


class AppStoreAppCurrentVersion(APIView):
    def get(self, request, country_code_alpha2, appstore_app_id):
        auth_data = {
            "country_code_alpha2": country_code_alpha2,
            "appstore_app_id": appstore_app_id,
        }
        store = AppStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class VivoStoreAppCurrentVersion(APIView):
    def get(self, request, vivo_store_app_id):
        auth_data = {
            "vivo_store_app_id": vivo_store_app_id,
        }
        store = VivoStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class HuaweiStoreAppCurrentVersion(APIView):
    def get(self, request):
        store_url = unquote(request.GET.get("store_url", ""))
        auth_data = {
            "store_url": store_url,
        }
        store = HuaweiStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class XiaomiStoreAppCurrentVersion(APIView):
    def get(self, request, xiaomi_store_app_id):
        auth_data = {
            "xiaomi_store_app_id": xiaomi_store_app_id,
        }
        store = XiaomiStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class YingyongbaoStoreAppCurrentVersion(APIView):
    def get(self, request):
        bundle_identifier = request.GET.get("bundle_identifier", "")
        auth_data = {
            "bundle_identifier": bundle_identifier,
        }
        store = YingyongbaoStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)
