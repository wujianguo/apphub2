from django.db import models


class VisibilityType(models.IntegerChoices):
    # Organization or application access must be granted explicitly to each user.
    Private = 1

    # The organization or application can be viewed by any logged in user.
    Internal = 2

    # The organization or application can be viewed without any authentication.
    Public = 3
