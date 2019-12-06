import pytest
import asyncio
from django.test import override_settings
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from graphene_django.settings import graphene_settings

from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer

from tests.models import SomeModel

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_schema_execution():
    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    s = SomeModel()
    await sync_to_async(s.save)()

    await communicator.receive_nothing(timeout=1)