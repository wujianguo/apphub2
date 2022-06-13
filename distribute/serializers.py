from email.policy import default
from django.db.models import Max
from django.urls import reverse
from django.core.signing import TimestampSigner
from rest_framework import serializers
from distribute.models import Package, Release, StoreApp, ReleaseStore
from distribute.stores.base import StoreType
from distribute.stores.store import get_store
from application.models import Application
from util.choice import ChoiceField
from util.url import build_absolute_uri

def compare_short_version(short_version1, short_version2):
    return True

class PackageSerializer(serializers.ModelSerializer):
    os = serializers.SerializerMethodField()
    install_url = serializers.SerializerMethodField()
    package_file = serializers.SerializerMethodField()
    icon_file = serializers.SerializerMethodField()
    uploader = serializers.SerializerMethodField()
    def get_os(self, obj):
        return ChoiceField(choices=Application.OperatingSystem.choices).to_representation(obj.app.os)

    def get_install_url(self, obj):
        if obj.app.os == Application.OperatingSystem.iOS:
            url_name = self.context['plist_url_name']
            namespace = self.context['namespace']
            path = self.context['path']
            signer = TimestampSigner()
            value = signer.sign(namespace+path+str(obj.package_id))
            value = value.split(':')[1:]
            location = reverse(url_name, args=(namespace, path, value[0], value[1], obj.package_id))
            return 'itms-services://?action=download-manifest&url=' + build_absolute_uri(location)
        else:
            return self.get_package_file(obj)

    def get_package_file(self, obj):
        return obj.package_file.url

    def get_icon_file(self, obj):
        if not obj.icon_file:
            return ''
        return obj.icon_file.url

    def get_uploader(self, obj):
        if obj.operator_content_type.model == 'appapitoken':
            return {
                'kind': 'Token',
                'name': obj.operator_content_object.name,
                'id': obj.operator_content_object.id
            }
        name = obj.operator_content_object.get_full_name()
        if not name:
            name = obj.operator_content_object.username
        return {
            'kind': 'User',
            'name': name,
            'username': obj.operator_content_object.username
        }

    class Meta:
        model = Package
        fields = ['uploader', 'name', 'install_url', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'package_id', 'size', 'bundle_identifier', 'commit_id', 'min_os', 'os', 'channle', 'description', 'update_time', 'create_time']
        read_only_fields = ['uploader', 'name', 'install_url', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'package_id', 'size', 'bundle_identifier', 'min_os', 'os', 'channle']

class PackageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['description', 'commit_id']

class UploadPackageSerializer(serializers.Serializer):
    file = serializers.FileField()
    description = serializers.CharField(default='')
    commit_id = serializers.CharField(max_length=40, default='')
    class Meta:
        fields = ['file', 'description', 'commit_id']

class RequestUploadPackageSerializer(serializers.Serializer):
    file_name = serializers.CharField(default='')
    description = serializers.CharField(default='')
    commit_id = serializers.CharField(max_length=16, default='')
    class Meta:
        fields = ['file_name', 'description', 'commit_id']

class UploadAliyunOssPackageSerializer(serializers.Serializer):
    object = serializers.CharField()
    description = serializers.CharField(default='')
    commit_id = serializers.CharField(max_length=16, default='')
    class Meta:
        fields = ['object', 'description', 'commit_id']

class ReleaseSerializer(serializers.ModelSerializer):
    os = serializers.SerializerMethodField()
    name = serializers.ReadOnlyField(source='package.name')
    fingerprint = serializers.ReadOnlyField(source='package.fingerprint')
    version = serializers.ReadOnlyField(source='package.version')
    short_version = serializers.ReadOnlyField(source='package.short_version')
    package_id = serializers.ReadOnlyField(source='package.package_id')
    size = serializers.ReadOnlyField(source='package.size')
    bundle_identifier = serializers.ReadOnlyField(source='package.bundle_identifier')
    commit_id = serializers.ReadOnlyField(source='package.commit_id')
    min_os = serializers.ReadOnlyField(source='package.min_os')
    channle = serializers.ReadOnlyField(source='package.channle')

    package_file = serializers.SerializerMethodField()
    icon_file = serializers.SerializerMethodField()

    def get_os(self, obj):
        return ChoiceField(choices=Application.OperatingSystem.choices).to_representation(obj.package.app.os)

    def get_package_file(self, obj):
        return obj.package.package_file.url

    def get_icon_file(self, obj):
        if not obj.package.icon_file:
            return ''
        return obj.package.icon_file.url

    class Meta:
        model = Release
        fields = ['os', 'release_id', 'release_notes', 'enabled', 'name', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'package_id', 'size', 'bundle_identifier', 'commit_id', 'min_os', 'channle', 'update_time', 'create_time']
        read_only_fields = ['os', 'release_id', 'name', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'package_id', 'size', 'bundle_identifier', 'commit_id', 'min_os', 'channle']

class ReleaseCreateSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
    enabled = serializers.BooleanField(help_text="This value determines the whether a release currently is enabled or disabled.")
    release_notes = serializers.CharField(required=False, max_length=1024, help_text="The release's release notes.")

    class Meta:
        fields = ['release_notes', 'enabled', 'package_id']

    def get_and_check_package(self, package_id, universal_app):
        try:
            package = Package.objects.get(package_id=package_id, app__universal_app=universal_app)
            try:
                Release.objects.get(package=package)
                raise serializers.ValidationError({'message': 'the package already released.'})
            except Release.DoesNotExist:
                pass
            try:
                Release.objects.get(package__version=package.version, package__short_version=package.short_version)
                raise serializers.ValidationError({'message': 'the version already released.'})
            except Release.DoesNotExist:
                pass
        except Package.DoesNotExist:
            raise serializers.ValidationError({'message': 'package_id is not found.'})
        return package

    def get_latest_packages(self, universal_app):
        packages = Package.objects.filter(app__universal_app=universal_app).order_by('-package_id')[:2]
        return packages

    def create(self, validated_data):
        universal_app = validated_data['universal_app']
        install_slug = universal_app.install_slug
        package_id = validated_data['package_id']
        package = self.get_and_check_package(package_id, universal_app)
        latest_packages = self.get_latest_packages(universal_app)
        latest_package = latest_packages.first()
        if latest_package is not None and not compare_short_version(package.short_version, latest_package.short_version):
            raise serializers.ValidationError({'message': 'short version should bigger than.'})
            
        # todo: check version
        if validated_data['enabled']:
            package.make_public(install_slug)

        release_id = Release.objects.filter(app__universal_app=universal_app).count() + 1
        app = package.app
        instance = Release.objects.create(
            app=app,
            package=package,
            release_id=release_id,
            release_notes=validated_data.get('release_notes', package.description),
            enabled=validated_data['enabled']
        )
        return instance

    def update(self, instance, validated_data):
        universal_app = validated_data['universal_app']
        install_slug = universal_app.install_slug
        release_notes = validated_data.get('validated_data', None)
        enabled = validated_data.get('enabled', None)
        package_id = validated_data.get('package_id', None)
        if enabled == instance.enabled:
            enabled = None

        package = None
        if package_id is not None:
            package = self.get_and_check_package(package_id, universal_app)
            if package.short_version != instance.package.short_version:
                latest_packages = self.get_latest_packages(universal_app)
                latest_package = latest_packages.first()
                if latest_package and latest_package.id != instance.package.id:
                    raise serializers.ValidationError({'message': 'package short version should equal with ' + instance.package.short_version})
                if latest_package and latest_package.id == instance.package.id:
                    if len(latest_packages) >= 2:
                        if compare_short_version(package.short_version, latest_packages[1].short_version):
                            raise serializers.ValidationError({'message': 'short version should bigger than.'})

        if release_notes is not None:
            instance.release_notes = release_notes

        if enabled is None and package is not None:
            if instance.enabled:
                instance.package.make_internal(install_slug)
                package.make_public(install_slug)
            instance.package = package
            instance.save()
            return instance

        if enabled is not None and package is None:
            if enabled:
                instance.package.make_public(install_slug)
            else:
                instance.package.make_internal(install_slug)
            instance.enabled = enabled
            instance.save()
            return instance

        if enabled is not None and enabled != instance.enabled and package is not None:
            if instance.enabled:
                instance.package.make_internal(install_slug)
            if enabled:
                package.make_public(install_slug)
            instance.enabled = enabled
            instance.package = package
            instance.save()
            return instance

        instance.save()
        return instance


class StoreAppSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    icon_file = serializers.SerializerMethodField()

    def get_name(self, obj):
        return get_store(obj.store).name()

    def get_display_name(self, obj):
        return get_store(obj.store).display_name()

    def get_icon_file(self, obj):
        return get_store(obj.store).icon()

    class Meta:
        model = StoreApp
        fields = ['name', 'display_name', 'icon_file', 'auth_data', 'current_version']

class StoreAppVivoAuthSerializer(serializers.Serializer):
    access_key = serializers.CharField()
    access_secret = serializers.CharField()
    vivo_store_app_id = serializers.CharField()
    store_app_link = serializers.URLField()
    class Meta:
        fields = ['access_key', 'access_secret', 'vivo_store_app_id', 'store_app_link']

    def create(self, validated_data):
        universal_app = validated_data['universal_app']
        app = universal_app.android
        store = StoreType.Vivo
        auth_data = {
            'access_key': validated_data['access_key'],
            'access_secret': validated_data['access_secret'],
            'vivo_store_app_id': validated_data['vivo_store_app_id'],
            'store_app_link': validated_data['store_app_link']
        }

        instance = StoreApp.objects.create(
            app=app,
            store=store,
            auth_data=auth_data,
        )
        return instance


class ReleaseStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseStore
        fields = ['name', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'package_id', 'size', 'bundle_identifier', 'commit_id', 'min_os', 'channle', 'release_store_id', 'release_notes', 'store', 'state', 'operator', 'update_time', 'create_time']

class ReleaseStoreCreateSerializer(serializers.Serializer):
    release_id = serializers.IntegerField()
    release_notes = serializers.CharField(required=False)
    store = ChoiceField(choices=StoreType.choices)

    class Meta:
        fields = ['release_id', 'release_notes', 'store']

    def create(self, validated_data):
        universal_app = validated_data['universal_app']
        release_id = validated_data['release_id']
        store = validated_data['store']
        state = ReleaseStore.State.SubmitReview
        group_id = ReleaseStore.objects.filter(release__app__universal_app=universal_app).aggregate(Max('group_id'))['group_id'] + 1
        operator = validated_data['operator']
        release_store_id = ReleaseStore.objects.filter(release__app__universal_app=universal_app).count() + 1
        try:
            release = Release.objects.get(app__universal_app=universal_app, release_id=release_id)
        except Release.DoesNotExist:
            raise serializers.ValidationError({'message': 'Release is not found.'})
        release_notes = validated_data.get('release_notes', release.release_notes)
        instance = ReleaseStore.objects.create(
            group_id=group_id,
            release_store_id=release_store_id,
            release=release,
            release_notes=release_notes,
            store=store,
            state=state,
            operator=operator
        )
        return instance

# class ReleaseStoreCancelSerializer(serializers.Serializer):
#     release_id = serializers.IntegerField()
#     release_notes = serializers.CharField()
#     state = ChoiceField(choices=ReleaseStore.State.choices)

#     class Meta:
#         fields = ['release_id', 'release_notes', 'state']

#     def create(self, validated_data):
#         pass

