from django.db import models

from graphene_subscriptions.mixins import SubscriptionModelMixin


class SomeModel(SubscriptionModelMixin, models.Model):
    name = models.CharField(max_length=50)
