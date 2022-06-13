import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from util.url import get_file_extension


def avatar_directory_path(instance, filename):
    name = '{0}.{1}'.format(instance.username, get_file_extension(filename))
    return 'users/{0}/avatar/{1}'.format(instance.id, name)

class User(AbstractUser):
    username = models.SlugField(max_length=150, unique=True)
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
