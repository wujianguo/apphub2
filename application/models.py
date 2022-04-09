from django.db import models
from django.conf import settings
from util.choice import CustomChoicesMeta, ChoiceField
from util.visibility import VisibilityType
from util.url import get_file_extension
from util.role import Role

def application_directory_path(instance, filename):
    name = 'icon.' + get_file_extension(filename)
    os = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(instance.os)
    if instance.universal_app.org is not None:
        return 'orgs/{0}/apps/{1}/{2}/icons/{3}'.format(instance.universal_app.org.id, instance.universal_app.id, os, name)
    else:
        return 'users/{0}/apps/{1}/{2}/icons/{3}'.format(instance.universal_app.owner.id, instance.universal_app.id, os, name)

def universal_app_directory_path(instance, filename):
    name = 'icon.' + get_file_extension(filename)
    if instance.org is not None:
        return 'orgs/{0}/apps/{1}/icons/{2}'.format(instance.org.id, instance.id, name)
    else:
        return 'users/{0}/apps/{1}/icons/{2}'.format(instance.owner.id, instance.id, name)

class Application(models.Model):
    class OperatingSystem(models.IntegerChoices, metaclass=CustomChoicesMeta):
        Android = 1
        iOS = 2
        Linux = 3
        macOS = 4
        tvOS = 5
        Windows = 6

    name = models.CharField(max_length=128, help_text='The descriptive name of the app')
    description = models.CharField(max_length=1024, help_text='A short text describing the app')
    icon_file = models.ImageField(upload_to=application_directory_path)
    os = models.IntegerField(choices=OperatingSystem.choices, help_text='The OS the app will be running on')
    universal_app = models.ForeignKey('application.UniversalApp', on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class UniversalApp(models.Model):
    iOS = models.OneToOneField(Application, blank=True, null=True, related_name='iOS', on_delete=models.SET_NULL)
    android = models.OneToOneField(Application, blank=True ,null=True, related_name='Android', on_delete=models.SET_NULL)
    macOS = models.OneToOneField(Application, blank=True, null=True, related_name='macOS', on_delete=models.SET_NULL)
    windows = models.OneToOneField(Application, blank=True, null=True, related_name='Windows', on_delete=models.SET_NULL)
    linux = models.OneToOneField(Application, blank=True, null=True, related_name='Linux', on_delete=models.SET_NULL)
    tvOS = models.OneToOneField(Application, blank=True, null=True, related_name='tvOS', on_delete=models.SET_NULL)
    path = models.SlugField(max_length=32, help_text='The path of the universal application.')
    name = models.CharField(max_length=128, help_text='The descriptive name of the app')
    description = models.CharField(max_length=1024, help_text='A short text describing the app')
    install_slug = models.SlugField(max_length=32, unique=True)
    icon_file = models.ImageField(upload_to=universal_app_directory_path)
    visibility = models.IntegerField(choices=VisibilityType.choices)
    org = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def enable_os_enum_list(self):
        ret = []
        choices = ChoiceField(choices=Application.OperatingSystem.choices)
        obj = self
        try:
            if obj.iOS:
                ret.append(choices.to_representation(Application.OperatingSystem.iOS))
        except:
            pass
        try:
            if obj.android:
                ret.append(choices.to_representation(Application.OperatingSystem.Android))
        except:
            pass
        try:
            if obj.macOS:
                ret.append(choices.to_representation(Application.OperatingSystem.macOS))
        except:
            pass
        try:
            if obj.windows:
                ret.append(choices.to_representation(Application.OperatingSystem.Windows))
        except:
            pass
        try:
            if obj.linux:
                ret.append(choices.to_representation(Application.OperatingSystem.Linux))
        except:
            pass
        try:
            if obj.tvOS:
                ret.append(choices.to_representation(Application.OperatingSystem.tvOS))
        except:
            pass
        return ret

class UniversalAppUser(models.Model):
    app = models.ForeignKey(UniversalApp, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.IntegerField(Role.choices)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class AppAPIToken(models.Model):
    app = models.ForeignKey(UniversalApp, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    token = models.CharField(max_length=16, unique=True)
    enable_upload_package = models.BooleanField(default=False)
    enable_get_packages = models.BooleanField(default=False)
    enable_get_releases = models.BooleanField(default=False)
    enable_get_upgrades = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

class Webhook(models.Model):
    app = models.ForeignKey(UniversalApp, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    url = models.URLField()
    auth_data = models.JSONField(default=dict)
    template = models.JSONField(default=dict)
    when_new_package = models.BooleanField(default=True)
    when_new_release = models.BooleanField(default=False)
    when_new_upgrade = models.BooleanField(default=False)
    when_store_state_change = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
