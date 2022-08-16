import hashlib

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

# from django.conf import settings
from application.models import Application
from distribute.stores.base import StoreType
from util.choice import ChoiceField
from util.url import get_file_extension

# from util.storage import make_directory, remove_directory, copy_file


def distribute_package_path(instance, filename):
    universal_app = instance.app.universal_app
    os = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(
        instance.app.os
    )
    name = (
        universal_app.path
        + "_"
        + instance.short_version
        + "_"
        + str(instance.package_id)
        + "."
        + get_file_extension(filename, "zip")
    )
    if universal_app.org is not None:
        return "orgs/{0}/apps/{1}/{2}/packages/{3}/{4}".format(
            universal_app.org.id, universal_app.id, os, instance.short_version, name
        )
    else:
        return "users/{0}/apps/{1}/{2}/packages/{3}/{4}".format(
            universal_app.owner.id, universal_app.id, os, instance.short_version, name
        )


def distribute_icon_path(instance, filename):
    universal_app = instance.app.universal_app
    os = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(
        instance.app.os
    )
    name = (
        universal_app.path
        + "_"
        + instance.short_version
        + "_"
        + str(instance.package_id)
        + "."
        + get_file_extension(filename)
    )
    if instance.app.universal_app.org is not None:
        return "orgs/{0}/apps/{1}/{2}/icons/{3}/{4}".format(
            universal_app.org.id, universal_app.id, os, instance.short_version, name
        )
    else:
        return "users/{0}/apps/{1}/{2}/icons/{3}/{4}".format(
            universal_app.owner.id, universal_app.id, os, instance.short_version, name
        )


class Package(models.Model):
    operator_content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    operator_object_id = models.PositiveIntegerField()
    operator_content_object = GenericForeignKey(
        "operator_content_type", "operator_object_id"
    )
    package_id = models.IntegerField()
    build_type = models.CharField(max_length=32, default="Debug")
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=32, help_text="The app's name (extracted from the uploaded package)."
    )
    package_file = models.FileField(upload_to=distribute_package_path)
    icon_file = models.FileField(upload_to=distribute_icon_path)
    fingerprint = models.CharField(
        max_length=32, help_text="MD5 checksum of the package binary."
    )
    version = models.CharField(
        max_length=64,
        help_text="The package's version.\nFor iOS: CFBundleVersion from info.plist.\nFor Android: android:versionCode from AppManifest.xml.",  # noqa: E501
    )
    short_version = models.CharField(
        max_length=64,
        help_text="The package's short version.\nFor iOS: CFBundleShortVersionString from info.plist.\nFor Android: android:versionName from AppManifest.xml.",  # noqa: E501
    )
    size = models.IntegerField(help_text="The package's size in bytes.")
    min_os = models.CharField(
        max_length=32, help_text="The package's minimum required operating system."
    )
    bundle_identifier = models.CharField(
        max_length=64, help_text="The identifier of the apps bundle."
    )
    extra = models.JSONField(default=dict)
    description = models.CharField(
        max_length=1024, help_text="The package's description."
    )
    commit_id = models.CharField(max_length=40)
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

    def make_public(self, install_slug):
        pass
        # self.make_package_file_public(self.package_file, install_slug)
        # self.make_package_file_public(self.icon_file, install_slug)

    def make_internal(self, install_slug):
        pass

    #     remove_directory(os.path.dirname(self.get_public_file_path(self.package_file, install_slug))) # noqa: E501

    # def make_package_file_public(self, file, install_slug):
    #     if not file.name:
    #         return
    #     initial_path = settings.MEDIA_ROOT + '/' + file.name
    #     new_name = self.get_public_file_path(file, install_slug)
    #     new_path = settings.MEDIA_ROOT + '/' + new_name
    #     make_directory(os.path.dirname(new_path))
    #     copy_file(initial_path, new_path)

    # def get_public_file_path(self, file, install_slug):
    #     os_name = ChoiceField(choices=Application.OperatingSystem.choices).to_representation(self.app.os) # noqa: E501
    #     return install_slug + '/' + os_name + '/' + self.short_version + '/' + self.name + '.' + get_file_extension(file.name, 'zip') # noqa: E501


class Release(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    package = models.OneToOneField(Package, on_delete=models.CASCADE)
    release_id = models.IntegerField()
    release_notes = models.CharField(
        max_length=1024, help_text="The release's release notes."
    )
    enabled = models.BooleanField(
        default=False,
        help_text="This value determines the whether a release currently is enabled or disabled.",  # noqa: E501
    )
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class Upgrade(models.Model):
    release = models.OneToOneField(Release, on_delete=models.CASCADE)
    release_notes = models.CharField(
        max_length=1024, help_text="The release's release notes."
    )
    upgrade_id = models.IntegerField()
    target_version = models.CharField(max_length=32)
    enabled = models.BooleanField(default=False)
    mandatory = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class StoreApp(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    store = models.IntegerField(choices=StoreType.choices)
    auth_data = models.JSONField(default=dict)
    current_version = models.CharField(max_length=64)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


# class ReleaseStore(models.Model):
#     class State(models.IntegerChoices):
#         Initial = 1
#         SubmitReview = 2
#         ReviewPassed = 3
#         ReviewRejected = 4
#         Released = 5

#     group_id = models.IntegerField()
#     release_store_id = models.IntegerField()
#     release = models.ForeignKey(Release, on_delete=models.CASCADE)
#     release_notes = models.CharField(max_length=1024, help_text="The release's release notes.") # noqa: E501
#     store = models.ForeignKey(StoreApp, on_delete=models.CASCADE)
#     state = models.IntegerField(choices=State.choices)
#     reason = models.JSONField(default=dict)
#     operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING) # noqa: E501
#     create_time = models.DateTimeField(auto_now_add=True)
#     update_time = models.DateTimeField(auto_now=True)

# class DistributeOperation(models.Model):
#     operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING) # noqa: E501
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')
#     operation = models.JSONField(default=dict)
#     create_time = models.DateTimeField(auto_now_add=True)
#     update_time = models.DateTimeField(auto_now=True)
