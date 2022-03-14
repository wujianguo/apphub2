import uuid, hashlib
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from application.models import UniversalApp, Application
from util.choice import ChoiceField

# alpha, beta, production, ...
class DeploymentEnvironment(models.Model):
    app = models.ForeignKey(UniversalApp, on_delete=models.CASCADE)
    name = models.SlugField(max_length=32)
    key = models.UUIDField(default=uuid.uuid4)

@receiver(post_save, sender=UniversalApp)
def notify_app_save(sender, instance, created, **kwargs):
    if not created:
        return
    DeploymentEnvironment.objects.bulk_create([
        DeploymentEnvironment(app=instance, name='alpha'),
        DeploymentEnvironment(app=instance, name='production')
    ])

def distribute_package_path(instance, filename):
    universal_app = instance.app.universal_app
    os = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(instance.app.os)
    name = universal_app.path + '_' + instance.short_version + '_' + str(instance.internal_build) + '.' + filename.split('.')[-1]
    if universal_app.org is not None:
      return 'orgs/{0}/apps/{1}/{2}/packages/{3}/{4}'.format(universal_app.org.id, universal_app.id, os, instance.short_version, name)
    else:
      return 'users/{0}/apps/{1}/{2}/packages/{3}/{4}'.format(universal_app.owner.id, universal_app.id, os, instance.short_version, name)

def distribute_icon_path(instance, filename):
    universal_app = instance.app.universal_app
    os = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(instance.app.os)
    name = universal_app.path + '_' + instance.short_version + '_' + str(instance.internal_build) + '.' + filename.split('.')[-1]
    if instance.app.universal_app.org is not None:
      return 'orgs/{0}/apps/{1}/{2}/icons/{3}/{4}'.format(universal_app.org.id, universal_app.id, os, instance.short_version, name)
    else:
      return 'users/{0}/apps/{1}/{2}/icons/{3}/{4}'.format(universal_app.owner.id, universal_app.id, os, instance.short_version, name)

class Package(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, help_text="The app's name (extracted from the uploaded package).")
    package_file = models.FileField(upload_to=distribute_package_path)
    icon_file = models.FileField(upload_to=distribute_icon_path)
    fingerprint = models.CharField(max_length=32, help_text="MD5 checksum of the package binary.")
    version = models.CharField(max_length=64, help_text="The package's version.\nFor iOS: CFBundleVersion from info.plist.\nFor Android: android:versionCode from AppManifest.xml.")
    short_version = models.CharField(max_length=64, help_text="The package's short version.\nFor iOS: CFBundleShortVersionString from info.plist.\nFor Android: android:versionName from AppManifest.xml.")
    internal_build = models.IntegerField()
    size = models.IntegerField(help_text="The package's size in bytes.")
    min_os = models.CharField(max_length=32, help_text="The package's minimum required operating system.")
    bundle_identifier = models.CharField(max_length=64, help_text="The identifier of the apps bundle.")
    extra = models.JSONField(default=dict)
    description = models.CharField(max_length=1024, help_text="The package's description.")
    commit_id = models.CharField(max_length=32)
    channle = models.CharField(max_length=32)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.package_file is not None:
            md5 = hashlib.md5()
            for chunk in self.package_file.chunks():
                md5.update(chunk)
            self.fingerprint = md5.hexdigest()
        super(Package, self).save(*args, **kwargs)
