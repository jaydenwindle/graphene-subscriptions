from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from graphene_subscriptions.serialize import serialize_value, deserialize_value


def trigger_subscription(group, value):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "subscription.triggered",
            "value": serialize_value(value),
            "group": group
        }
    )
