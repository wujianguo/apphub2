from django.db import models


class Role(models.IntegerChoices):
    Owner = 1
    Manager = 2
    Developer = 3
    Tester = 4
