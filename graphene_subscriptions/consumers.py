import functools

from graphene_django.settings import graphene_settings
from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from rx.subjects import Subject

from graphene_subscriptions.events import SubscriptionEvent


stream = Subject()


# GraphQL types might use info.context.user to access currently authenticated user.
# When Query is called, info.context is request object,
# however when Subscription is called, info.context is scope dict.
# This is minimal wrapper around dict to mimic object behavior.
class AttrDict:
    def __init__(self, data):
        self.data = data or {}

    def __getattr__(self, item):
        return self.get(item)

    def get(self, item):
        return self.data.get(item)


class GraphqlSubscriptionConsumer(JsonWebsocketConsumer):
    groups = []

    def subscribe(self, name):
        if name not in self.groups:
            self.groups.append(name)
            async_to_sync(self.channel_layer.group_add)(name, self.channel_name)

    def connect(self):
        self.subscribe('subscriptions')

        self.scope['subscribe'] = self.subscribe
        self.accept("graphql-ws")

    def disconnect(self, close_code):
        for group in self.groups:
            async_to_sync(self.channel_layer.group_discard)(
                group,
                self.channel_name
            )

    def receive_json(self, request):
        id = request.get("id")

        if request["type"] == "connection_init":
            return

        elif request["type"] == "start":
            payload = request["payload"]
            context = AttrDict(self.scope)

            schema = graphene_settings.SCHEMA

            result = schema.execute(
                payload["query"],
                operation_name=payload.get("operationName"),
                variables=payload.get("variables"),
                context=context,
                root=stream,
                allow_subscriptions=True,
            )

            if hasattr(result, "subscribe"):
                result.subscribe(functools.partial(self._send_result, id))
            else:
                self._send_result(id, result)

        elif request["type"] == "stop":
            pass

    def signal_fired(self, message):
        stream.on_next(SubscriptionEvent.from_dict(message["event"]))

    def _send_result(self, id, result):
        errors = result.errors

        self.send_json(
            {
                "id": id,
                "type": "data",
                "payload": {
                    "data": result.data,
                    "errors": list(map(str, errors)) if errors else None,
                },
            }
        )
