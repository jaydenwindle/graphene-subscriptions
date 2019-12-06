from django.db.models.signals import post_save, post_delete
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from graphene_subscriptions.events import (
    ModelSubscriptionEvent,
    CREATED,
    UPDATED,
    DELETED,
)


def post_save_subscription(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()

    event = ModelSubscriptionEvent(
        operation=CREATED if created else UPDATED, instance=instance
    )

    async_to_sync(channel_layer.group_send)(
        "subscriptions", {"type": "signal.fired", "event": event.to_dict()}
    )


def post_delete_subscription(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    event = ModelSubscriptionEvent(operation=DELETED, instance=instance)

    async_to_sync(channel_layer.group_send)(
        "subscriptions", {"type": "signal.fired", "event": event.to_dict()}
    )


# post_save.connect(post_save_subscription, dispatch_uid="post_save_subscription")
# post_delete.connect(post_delete_subscription, dispatch_uid="post_save_subscription")
