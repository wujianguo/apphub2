from rest_framework import serializers
from distribute.models import Package


class PackageSerializer(serializers.ModelSerializer):
    icon_file = serializers.SerializerMethodField()
    package_file = serializers.SerializerMethodField()

    def get_icon_file(self, obj):
        return ''

    def get_package_file(self, obj):
        return ''

    class Meta:
        model = Package
        fields = ['name', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'internal_build', 'size', 'bundle_identifier', 'commit_id', 'min_os', 'channle', 'description', 'update_time', 'create_time']
        read_only_fields = ['name', 'package_file', 'icon_file', 'fingerprint', 'version', 'short_version', 'internal_build', 'size', 'bundle_identifier', 'min_os', 'channle']

class PackageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['description', 'commit_id']

class UploadPackageSerializer(serializers.Serializer):
    file = serializers.FileField()
    class Meta:
        fields = ['file']
