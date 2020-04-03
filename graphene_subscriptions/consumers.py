import functools

from graphene_django.settings import graphene_settings
from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from rx.subjects import Subject

from io import BytesIO
from channels.http import AsgiRequest

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from django.db import close_old_connections

from graphene_subscriptions.events import deserialize_value


class GraphqlSubscriptionConsumer(JsonWebsocketConsumer):
    groups = {}

    def subscribe(self, name):
        stream = Subject()
        if name not in self.groups:
            self.groups[name] = stream
            async_to_sync(self.channel_layer.group_add)(name, self.channel_name)
        return stream

    def connect(self):
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
            headers = dict(request["payload"])
            if "Authorization" in headers:
                    token_name, token_key = headers["Authorization"].split()
                    if token_name == "JWT":
                        token = jwt_decode(
                            token_key,
                            settings.SECRET_KEY,
                            algorithms=["HS256"]
                        )
                        self.user = get_user_model().objects.get(
                            username=token["username"]
                        )
                        close_old_connections()
            return

        elif request["type"] == "start":
            
            payload = request["payload"]

            temp = {}
            for x, y in self.scope["headers"]:
                temp[x.decode()]=y
            self.scope["headers"] = temp

            self.scope["method"] = "WebSocket"

            context = AsgiRequest(self.scope, BytesIO(b""))

            context.user = self.user 

            schema = graphene_settings.SCHEMA

            result = schema.execute(
                payload["query"],
                operation_name=payload.get("operationName"),
                variables=payload.get("variables"),
                context=context,
                root=self,
                allow_subscriptions=True,
            )

            if hasattr(result, "subscribe"):
                result.subscribe(functools.partial(self._send_result, id))
            else:
                self._send_result(id, result)

        elif request["type"] == "stop":
            pass

    def subscription_triggered(self, message):

        group = message['group']

        if group in self.groups:
            stream = self.groups[group] 
            value = deserialize_value(message['value'])

            stream.on_next(value)

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
