import time
import pytest
import asyncio
from django.test import override_settings
from django.db.models.signals import post_save, post_delete
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from graphene_django.settings import graphene_settings

from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer
from graphene_subscriptions.signals import (
    post_delete_subscription,
    post_save_subscription,
)

from tests.models import SomeModel


async def query(query, communicator):
    await communicator.send_json_to(
        {"id": 1, "type": "start", "payload": {"query": query}}
    )


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_schema_execution_works():
    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    subscription = """
        subscription {
            hello
        }
    """

    await query(subscription, communicator)

    response = await communicator.receive_json_from()

    assert response["payload"] == {"data": {"hello": "hello world!"}, "errors": None}


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_created_subscription_succeeds():
    post_save.connect(
        post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_save"
    )

    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    subscription = """
        subscription {
            someModelCreated {
                name
            }
        }
    """

    await query(subscription, communicator)

    s = await sync_to_async(SomeModel.objects.create)(name="test name")

    response = await communicator.receive_json_from()

    assert response["payload"] == {
        "data": {"someModelCreated": {"name": s.name}},
        "errors": None,
    }

    post_save.disconnect(
        post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_save"
    )


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_updated_subscription_succeeds():
    post_save.connect(
        post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
    )

    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    s = await sync_to_async(SomeModel.objects.create)(name="test name")

    subscription = (
        """
        subscription {
            someModelUpdated(id: %d) {
                name
            }
        }
    """
        % s.pk
    )

    await query(subscription, communicator)

    await sync_to_async(s.save)()

    response = await communicator.receive_json_from()

    assert response["payload"] == {
        "data": {"someModelUpdated": {"name": s.name}},
        "errors": None,
    }

    post_save.disconnect(
        post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
    )


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_deleted_subscription_succeeds():
    post_delete.connect(
        post_delete_subscription,
        sender=SomeModel,
        dispatch_uid="some_model_post_delete",
    )

    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    s = await sync_to_async(SomeModel.objects.create)(name="test name")

    subscription = (
        """
        subscription {
            someModelDeleted(id: %d) {
                name
            }
        }
    """
        % s.pk
    )

    await query(subscription, communicator)

    await sync_to_async(s.delete)()

    response = await communicator.receive_json_from()

    assert response["payload"] == {
        "data": {"someModelDeleted": {"name": s.name}},
        "errors": None,
    }

    post_delete.disconnect(
        post_delete_subscription,
        sender=SomeModel,
        dispatch_uid="some_model_post_delete",
    )