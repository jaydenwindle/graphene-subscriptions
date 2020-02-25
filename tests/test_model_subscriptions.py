import pytest
import asyncio
import graphene

from django.test import override_settings	
from django.db.models.signals import post_save, post_delete
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer
from graphene_subscriptions.events import trigger_subscription, serialize_value

from tests.models import SomeModel
from tests.schema import CUSTOM_EVENT


async def subscribe(query, variables=None):
    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to(
        {"id": 1, "type": "start", "payload": {"query": query, "variables": variables}}
    )

    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_schema_execution_works():
    query = """
        subscription {
            hello
        }
    """

    subscription = await subscribe(query)

    response = await subscription.receive_json_from()

    assert response["payload"] == {"data": {"hello": "hello world!"}, "errors": None}

    await subscription.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_custom_subscription_works():
    query = """
        subscription {
            customSubscription
        }
    """

    subscription = await subscribe(query)

    await asyncio.sleep(0.01)

    await sync_to_async(trigger_subscription)('customSubscription', 'success')

    response = await subscription.receive_json_from()

    assert response['payload']['data']['customSubscription'] == 'success'


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_created_subscription():
    query = """
        subscription {
            someModelCreated {
                id
                name
            }
        }
    """

    subscription = await subscribe(query)

    await asyncio.sleep(0.01)

    instance = await database_sync_to_async(SomeModel.objects.create)(name="test 123")

    response = await subscription.receive_json_from()

    assert response['payload']['data']['someModelCreated']['id'] == str(instance.pk)
    assert response['payload']['data']['someModelCreated']['name'] == "test 123"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_updated_subscription():
    query = """
        subscription SomeModelUpdated($id: String) {
            someModelUpdated(id: $id) {
                id
                name
            }
        }
    """

    instance = await database_sync_to_async(SomeModel.objects.create)(name="test 123")

    subscription = await subscribe(query, { "id": instance.pk })

    await asyncio.sleep(0.01)

    instance.name = "test 234"
    await database_sync_to_async(instance.save)()

    response = await subscription.receive_json_from()

    assert response['payload']['data']['someModelUpdated']['id'] == str(instance.pk)
    assert response['payload']['data']['someModelUpdated']['name'] == "test 234"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_deleted_subscription():
    query = """
        subscription SomeModelDeleted($id: String) {
            someModelDeleted(id: $id) {
                id
                name
            }
        }
    """
    instance = await database_sync_to_async(SomeModel.objects.create)(name="test 123")

    subscription = await subscribe(query, { "id": instance.pk })

    await asyncio.sleep(0.01)

    instance_pk = instance.pk

    await database_sync_to_async(instance.delete)()

    response = await subscription.receive_json_from()

    assert response['payload']['data']['someModelDeleted']['id'] == str(instance_pk)
    assert response['payload']['data']['someModelDeleted']['name'] == "test 123"
