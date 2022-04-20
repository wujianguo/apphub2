import os.path
from rest_framework import serializers
from django.urls import reverse
from organization.models import Organization, OrganizationUser
from util.choice import ChoiceField
from util.visibility import VisibilityType
from util.role import Role
from util.url import build_absolute_uri

class OrganizationSerializer(serializers.ModelSerializer):
    path = serializers.SlugField(max_length=32, help_text='The path of the organization.')
    name = serializers.CharField(max_length=128, help_text='A short text describing the organization')
    description = serializers.CharField(max_length=1024, required=False, help_text='A short text describing the organization')
    visibility = ChoiceField(VisibilityType.choices)
    icon_file = serializers.SerializerMethodField()

    def get_icon_file(self, obj):
        location = reverse('org-icon', args=(obj.path, os.path.basename(obj.icon_file.name)))
        return build_absolute_uri(location)

    class Meta:
        model = Organization
        fields = ['path', 'name', 'description', 'visibility', 'icon_file', 'update_time', 'create_time']

class OrganizationIconSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ['icon_file']

class UserOrganizationSerializer(serializers.ModelSerializer):
    path = serializers.StringRelatedField(source='org.path', help_text='The path of the organization.')
    name = serializers.StringRelatedField(source='org.name', help_text='A short text describing the organization.')
    description = serializers.StringRelatedField(source='org.description', required=False, help_text='A short text describing the organization')
    visibility = ChoiceField(VisibilityType.choices, source='org.visibility')
    role = ChoiceField(choices=Role.choices, required=False)
    update_time = serializers.ReadOnlyField(source='org.update_time')
    create_time = serializers.ReadOnlyField(source='org.create_time')
    icon_file = serializers.SerializerMethodField()

    def get_icon_file(self, obj):
        location = reverse('org-icon', args=(obj.org.path, os.path.basename(obj.org.icon_file.name)))
        return build_absolute_uri(location)

    class Meta:
        model = OrganizationUser
        fields = ['role', 'path', 'name', 'description', 'visibility', 'icon_file', 'update_time', 'create_time']

class OrganizationUserSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    role = ChoiceField(choices=Role.choices)

    class Meta:
        model = OrganizationUser
        fields = ['role', 'username', 'update_time', 'create_time']
        read_only_fields = ['username', 'update_time', 'create_time']

class OrganizationUserAddSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = ChoiceField(choices=Role.choices)

    class Meta:
        fields = ['role', 'username']
