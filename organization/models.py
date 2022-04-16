from django.db import models
from django.conf import settings
from util.visibility import VisibilityType
from util.url import get_file_extension
from util.role import Role


def organization_directory_path(instance, filename):
    name = 'icon.' + get_file_extension(filename)
    return 'internal/orgs/{0}/icons/{1}'.format(instance.id, name)

class Organization(models.Model):
    path = models.SlugField(max_length=32, unique=True, help_text='The path of the organization.')
    name = models.CharField(max_length=128, help_text='The descriptive name of the organization')
    description = models.CharField(max_length=1024, help_text='A short text describing the organization')
    visibility = models.IntegerField(choices=VisibilityType.choices)
    icon_file = models.ImageField(upload_to=organization_directory_path)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class OrganizationUser(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.IntegerField(Role.choices)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
