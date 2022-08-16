from django.contrib.auth.models import AbstractUser
from django.db import models

from util.url import get_file_extension


def avatar_directory_path(instance, filename):
    name = "{0}.{1}".format(instance.username, get_file_extension(filename))
    return "users/{0}/avatar/{1}".format(instance.id, name)


class User(AbstractUser):
    username = models.SlugField(max_length=150, unique=True)
    avatar = models.ImageField(upload_to=avatar_directory_path)
