from datetime import timedelta
from urllib.parse import unquote

from django.conf import settings
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
                                     check_app_view_permission, get_app)
from application.serializers import UniversalAppSerializer
from distribute.models import (FileUploadRecord, Package, Release, StoreApp,
                               StoreAppVersionRecord)
from distribute.package_parser import parser
from distribute.serializers import (PackageSerializer, PackageUpdateSerializer,
                                    ReleaseCreateSerializer, ReleaseSerializer,
                                    RequestUploadPackageSerializer,
                                    StoreAppAppStoreAuthSerializer,
                                    StoreAppHuaweiStoreAuthSerializer,
                                    StoreAppSerializer,
                                    StoreAppVersionSerializer,
                                    StoreAppVivoAuthSerializer,
                                    StoreAppXiaomiStoreAuthSerializer,
                                    StoreAppYingyongbaoStoreAuthSerializer,
                                    UploadPackageSerializer)
from distribute.stores.app_store import AppStore
from distribute.stores.base import StoreType
from distribute.stores.huawei import HuaweiStore
from distribute.stores.store import get_store
from distribute.stores.vivo import VivoStore
from distribute.stores.xiaomi import XiaomiStore
from distribute.stores.yingyongbao import YingyongbaoStore
from distribute.task import notify_new_package
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


def create_package(
    operator_content_object,
    universal_app,
    file,
    commit_id="",
    description="",
    channel="",
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
        channel=channel,
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
    notify_new_package(instance.id)
    return instance


class UserAppPackageUpload(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def url_name(self):
        return "user-app-package"

    def plist_url_name(self):
        return "user-app-package-plist"

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
        channel = serializer.validated_data.get("channel", "")
        app = self.check_and_get_app(request, namespace, path)
        instance = create_package(
            request.user, app, file, commit_id, description, channel, build_type
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
        channel = serializer.validated_data.get("channel", "")
        instance = create_package(
            request.token, app, file, commit_id, description, channel, build_type
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


class RequestUploadPackage(APIView):
    permission_classes = [UploadPackagePermission]

    def post(self, request):
        serializer = RequestUploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        app = request.token.app
        filename = serializer.validated_data["filename"]
        description = serializer.validated_data.get("description", "")
        commit_id = serializer.validated_data.get("commit_id", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        channel = serializer.validated_data.get("channel", "")

        ret = default_storage.request_upload_url(app.install_slug, filename)
        data = {
            "type": "package",
            "file": ret["file"],
            "description": description,
            "commit_id": commit_id,
            "build_type": build_type,
            "channel": channel,
            "uploader_type": "token",
            "uploader_id": request.token.id
        }
        instance = FileUploadRecord.objects.create(
            universal_app=app,
            data=data
        )
        ret["record_id"] = instance.id
        ret["storage"] = settings.STORAGE_TYPE
        return Response(ret)


class CheckUploadPackage(APIView):
    permission_classes = [UploadPackagePermission]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, record_id):
        app = request.token.app
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            data = {
                "status": "waiting"  # expired
            }

        return Response(data)

    def post(self, request, record_id):
        app = request.token.app
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            extra = record.data
            file = default_storage.open(extra["file"])
            commit_id = extra.get("commit_id", "")
            description = extra.get("description", "")
            build_type = extra.get("build_type", "Debug")
            channel = extra.get("channel", "")
            uploader = AppAPIToken.objects.get(id=extra["uploader_id"])
            instance = create_package(
                uploader, app, file, commit_id, description, channel, build_type
            )
            record.package = instance
            try:
                default_storage.delete(extra["file"])
            except:   # noqa: E722
                pass
            record.save()
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(instance, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }

        return Response(data)


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


class UserStoreAppList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        store_app_list = StoreApp.objects.filter(app__universal_app=app)
        serializer = StoreAppSerializer(store_app_list, many=True)
        return Response(serializer.data)


class OrganizationStoreAppList(UserStoreAppList):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def store_type(self):
        pass

    def get_serializer(self, data):
        pass

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        try:
            store_app = StoreApp.objects.get(app__universal_app=app, store=self.store_type())  # noqa: E501
        except StoreApp.DoesNotExist:
            raise Http404
        serializer = StoreAppSerializer(store_app)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        try:
            StoreApp.objects.get(app__universal_app=app, store=self.store_type())
            return Response({}, status=status.HTTP_409_CONFLICT)
        except StoreApp.DoesNotExist:
            pass
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        data = StoreAppSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationStoreAppBase(UserStoreAppBase):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppAppstore(UserStoreAppBase):

    def store_type(self):
        return StoreType.AppStore

    def get_serializer(self, data):
        return StoreAppAppStoreAuthSerializer(data=data)


class OrganizationStoreAppAppstore(UserStoreAppAppstore):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppVivo(UserStoreAppBase):

    def store_type(self):
        return StoreType.Vivo

    def get_serializer(self, data):
        return StoreAppVivoAuthSerializer(data=data)


class OrganizationStoreAppVivo(UserStoreAppVivo):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppHuawei(UserStoreAppBase):

    def store_type(self):
        return StoreType.Huawei

    def get_serializer(self, data):
        return StoreAppHuaweiStoreAuthSerializer(data=data)


class OrganizationStoreAppHuawei(UserStoreAppHuawei):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppXiaomi(UserStoreAppBase):

    def store_type(self):
        return StoreType.Xiaomi

    def get_serializer(self, data):
        return StoreAppXiaomiStoreAuthSerializer(data=data)


class OrganizationStoreAppXiaomi(UserStoreAppXiaomi):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppYingyongbao(UserStoreAppBase):

    def store_type(self):
        return StoreType.Yingyongbao

    def get_serializer(self, data):
        return StoreAppYingyongbaoStoreAuthSerializer(data=data)


class OrganizationStoreAppYingyongbao(UserStoreAppYingyongbao):
    def get_namespace(self, path):
        return Namespace.organization(path)


def update_store_app_current_version(store_app):
    store = get_store(store_app.store)(store_app.auth_data)
    try:
        data = store.store_current()
        version = data["version"]
        if not version:
            return None
    except:  # noqa: E722
        return None

    try:
        ret = StoreAppVersionRecord.objects.get(
            app=store_app.app,
            store=store_app.store,
            short_version=version)
        ret.save()
    except StoreAppVersionRecord.DoesNotExist:
        ret = StoreAppVersionRecord.objects.create(
            app=store_app.app,
            store=store_app.store,
            short_version=version)
    return ret


class UserStoreAppCurrentVersion(APIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        stores = [
            StoreType.AppStore,
            StoreType.Huawei,
            StoreType.Vivo,
            StoreType.Xiaomi,
            StoreType.Yingyongbao
        ]
        versions = []
        for store in stores:
            ret = StoreAppVersionRecord.objects.filter(
                app__universal_app=app,
                store=store).order_by("-update_time").first()
            if ret:
                versions.append(ret)
        serializer = StoreAppVersionSerializer(versions, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        stores = [
            StoreType.AppStore,
            StoreType.Huawei,
            StoreType.Vivo,
            StoreType.Xiaomi,
            StoreType.Yingyongbao
        ]

        versions = []
        for store in stores:
            try:
                store_app = StoreApp.objects.get(app__universal_app=app, store=store)
            except StoreApp.DoesNotExist:
                continue

            ret = update_store_app_current_version(store_app)
            if ret:
                versions.append(ret)

        serializer = StoreAppVersionSerializer(versions, many=True)
        return Response(serializer.data)


class OrganizationStoreAppCurrentVersion(UserStoreAppCurrentVersion):

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
