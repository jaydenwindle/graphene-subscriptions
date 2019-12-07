from django.db.models.signals import post_save, post_delete

from graphene_subscriptions.events import (
    ModelSubscriptionEvent,
    CREATED,
    UPDATED,
    DELETED,
)


def post_save_subscription(sender, instance, created, **kwargs):
    event = ModelSubscriptionEvent(
        operation=CREATED if created else UPDATED, instance=instance
    )
    event.send()


def post_delete_subscription(sender, instance, **kwargs):
    event = ModelSubscriptionEvent(operation=DELETED, instance=instance)
    event.send()
