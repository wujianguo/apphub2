from rest_framework import serializers
from application.models import Application, UniversalApp, UniversalAppUser
from util.choice import ChoiceField
from util.visibility import VisibilityType

class UniversalAppSerializer(serializers.ModelSerializer):
    path = serializers.SlugField(max_length=32, help_text='The path of the universal application.')
    name = serializers.CharField(max_length=128, help_text='The descriptive name of the app')
    description = serializers.CharField(required=False, max_length=1024, help_text='A short text describing the application')
    visibility = ChoiceField(VisibilityType.choices)
    enable_os = serializers.SerializerMethodField()
    namespace = serializers.SerializerMethodField()

    def get_enable_os(self, obj):
        return obj.enable_os_enum_list()

    def get_namespace(self, obj):
        if obj.owner:
            return {
                'path': obj.owner.username,
                'kind': 'User'
            }
        if obj.org:
            return {
                'path': obj.org.path,
                'kind': 'Organization'
            }

    class Meta:
        model = UniversalApp
        fields = ['namespace', 'path', 'name', 'description', 'visibility', 'enable_os', 'update_time', 'create_time']

class UniversalAppCreateSerializer(serializers.Serializer):
    path = serializers.SlugField(max_length=32, help_text='The path of the universal application.')
    name = serializers.CharField(max_length=128, help_text='The descriptive name of the app')
    install_slug = serializers.SlugField(max_length=32)
    description = serializers.CharField(required=False, max_length=1024, help_text='A short text describing the application')
    visibility = ChoiceField(VisibilityType.choices)
    enable_os = serializers.ListField(child=ChoiceField(choices=Application.OperatingSystem.choices), allow_empty=False)

    class Meta:
        fields = ['path', 'name', 'description', 'visibility', 'enable_os']

    def create(self, validated_data):
        instance = UniversalApp.objects.create(
            path=validated_data['path'],
            name=validated_data['name'],
            install_slug=validated_data['install_slug'],
            description=validated_data.get('description', ''),
            visibility=validated_data['visibility'],
            owner=validated_data.get('owner', None),
            org=validated_data.get('org', None)
        )

        enable_os = validated_data['enable_os']
        iOS = None
        android = None
        macOS = None
        windows = None
        linux = None
        tvOS = None

        for os in enable_os:
            if os == Application.OperatingSystem.iOS:
                iOS = Application.objects.create(os=Application.OperatingSystem.iOS, universal_app=instance)
            if os == Application.OperatingSystem.Android:
                android = Application.objects.create(os=Application.OperatingSystem.Android, universal_app=instance)
            if os == Application.OperatingSystem.macOS:
                macOS = Application.objects.create(os=Application.OperatingSystem.macOS, universal_app=instance)
            if os == Application.OperatingSystem.Windows:
                windows = Application.objects.create(os=Application.OperatingSystem.Windows, universal_app=instance)
            if os == Application.OperatingSystem.Linux:
                linux = Application.objects.create(os=Application.OperatingSystem.Linux, universal_app=instance)
            if os == Application.OperatingSystem.tvOS:
                tvOS = Application.objects.create(os=Application.OperatingSystem.tvOS, universal_app=instance)
        instance.iOS = iOS
        instance.android = android
        instance.macOS = macOS
        instance.windows = windows
        instance.linux = linux
        instance.tvOS = tvOS
        instance.save()
        return instance

class UniversalAppIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniversalApp
        fields = ['icon_file']

class UserUniversalAppSerializer(serializers.ModelSerializer):
    path = serializers.StringRelatedField(source='app.path')
    name = serializers.StringRelatedField(source='app.name')
    description = serializers.StringRelatedField(source='app.description')
    visibility = ChoiceField(VisibilityType.choices, source='app.visibility')
    role = ChoiceField(choices=UniversalAppUser.ApplicationUserRole.choices)
    update_time = serializers.ReadOnlyField(source='app.update_time')
    create_time = serializers.ReadOnlyField(source='app.create_time')
    enable_os = serializers.SerializerMethodField()
    namespace = serializers.SerializerMethodField()

    def get_enable_os(self, obj):
        return obj.app.enable_os_enum_list()

    def get_namespace(self, obj):
        if obj.app.owner:
            return {
                'path': obj.app.owner.username,
                'kind': 'User'
            }
        if obj.app.org:
            return {
                'path': obj.app.org.path,
                'kind': 'Organization'
            }

    class Meta:
        model = UniversalAppUser
        fields = ['role', 'namespace', 'path', 'name', 'description', 'visibility', 'enable_os', 'update_time', 'create_time']

class UniversalAppUserSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    role = ChoiceField(choices=UniversalAppUser.ApplicationUserRole.choices)

    class Meta:
        model = UniversalAppUser
        fields = ['role', 'username', 'update_time', 'create_time']

class UniversalAppUserAddSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = ChoiceField(choices=UniversalAppUser.ApplicationUserRole.choices)

    class Meta:
        fields = ['role', 'username']
