from django.db import models


class SomeModel(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)

