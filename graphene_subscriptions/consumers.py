import functools
import json

from graphene_django.settings import graphene_settings
from rx.subject import Subject

from graphene_subscriptions.events import SubscriptionEvent
from channels.generic.websocket import AsyncWebsocketConsumer
from graphql import execute

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


class GraphqlSubscriptionConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add("subscriptions", self.channel_name)
        await self.accept("graphql-ws")

    async def disconnect(self, close_code):
        await self.send({"type": "websocket.close", "code": 1000})

    async def receive(self, text_data):
        request = json.loads(text_data)
        id = request.get("id")

        if request["type"] == "connection_init":
            return

        elif request["type"] == "start":
            payload = request["payload"]
            context = AttrDict(self.scope)

            schema = graphene_settings.SCHEMA
            variables = payload.get("variables")

            result = await execute(
                schema,
                payload["query"],
                operation_name=payload.get("operationName"),
                variable_values=variables,
                context_value=context,
                root_value=None,
            )

            if hasattr(result, "subscribe"):
                result.subscribe(functools.partial(self._send_result, id))
            else:
                await self._send_result(id, result)

        elif request["type"] == "stop":
            pass

    async def signal_fired(self, event):
        stream.on_next(SubscriptionEvent.from_dict(event["event"]))

    async def _send_result(self, id, result):
        errors = result.errors

        await self.send(
            {
                "type": "websocket.send",
                "text": json.dumps(
                    {
                        "id": id,
                        "type": "data",
                        "payload": {
                            "data": result.data,
                            "errors": list(map(str, errors)) if errors else None,
                        },
                    }
                ),
            }
        )