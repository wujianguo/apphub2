from rest_framework import serializers
# from rest_framework.validators import UniqueValidator
from organization.models import Organization, OrganizationUser
from util.choice import ChoiceField
from util.visibility import VisibilityType
from util.role import Role

class OrganizationSerializer(serializers.ModelSerializer):
    # validators=[UniqueValidator(queryset=Organization.objects.all())])
    path = serializers.SlugField(max_length=32, help_text='The path of the organization.')
    name = serializers.CharField(max_length=128, help_text='A short text describing the organization')
    description = serializers.CharField(max_length=1024, required=False, help_text='A short text describing the organization')
    visibility = ChoiceField(VisibilityType.choices)

    class Meta:
        model = Organization
        fields = ['path', 'name', 'description', 'visibility', 'update_time', 'create_time']

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

    class Meta:
        model = OrganizationUser
        fields = ['role', 'path', 'name', 'description', 'visibility', 'update_time', 'create_time']

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
