import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


def avatar_directory_path(instance, filename):
    name = '{0}.{1}'.format(instance.username, filename.split('.')[-1])
    return 'users/{0}/avatar/{1}'.format(instance.id, name)

class User(AbstractUser):
    email_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to=avatar_directory_path)

class EmailCode(models.Model):
    class EmailCodeType(models.IntegerChoices):
        VerifyEmail = 1
        ResetPassword = 2

    email = models.EmailField()
    code = models.UUIDField(default=uuid.uuid4)
    valid = models.BooleanField(default=True)
    verify_count = models.IntegerField(default=0)
    type = models.IntegerField(choices=EmailCodeType.choices)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
