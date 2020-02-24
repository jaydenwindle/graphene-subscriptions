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
async def test_group_subscription_works():
    query = """
        subscription {
            testSubscription
        }
    """

    subscription = await subscribe(query)

    await asyncio.sleep(0.01)

    await sync_to_async(trigger_subscription)('testSubscription', 'success')

    response = await subscription.receive_json_from()

    assert response['payload']['data']['testSubscription'] == 'success'

# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_model_created_subscription_succeeds():
#     post_save.connect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_save"
#     )

#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     subscription = """
#         subscription {
#             someModelCreated {
#                 name
#             }
#         }
#     """

#     await query(subscription, communicator)

#     s = await database_sync_to_async(SomeModel.objects.create)(name="test name")

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"someModelCreated": {"name": s.name}},
#         "errors": None,
#     }

#     await communicator.disconnect()

#     post_save.disconnect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_save"
#     )


# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_model_updated_subscription_succeeds():
#     post_save.connect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
#     )

#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     s = await database_sync_to_async(SomeModel.objects.create)(name="test name")

#     subscription = (
#         """
#         subscription {
#             someModelUpdated(id: %d) {
#                 name
#             }
#         }
#     """
#         % s.pk
#     )

#     await query(subscription, communicator)

#     await database_sync_to_async(s.save)()

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"someModelUpdated": {"name": s.name}},
#         "errors": None,
#     }

#     await communicator.disconnect()

#     post_save.disconnect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
#     )


# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_model_deleted_subscription_succeeds():
#     post_delete.connect(
#         post_delete_subscription,
#         sender=SomeModel,
#         dispatch_uid="some_model_post_delete",
#     )

#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     s = await database_sync_to_async(SomeModel.objects.create)(name="test name")

#     subscription = (
#         """
#         subscription {
#             someModelDeleted(id: %d) {
#                 name
#             }
#         }
#     """
#         % s.pk
#     )

#     await query(subscription, communicator)

#     await database_sync_to_async(s.delete)()

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"someModelDeleted": {"name": s.name}},
#         "errors": None,
#     }

#     await communicator.disconnect()

#     post_delete.disconnect(
#         post_delete_subscription,
#         sender=SomeModel,
#         dispatch_uid="some_model_post_delete",
#     )


# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_model_subscription_with_variables_succeeds():
#     post_save.connect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
#     )

#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     s = await database_sync_to_async(SomeModel.objects.create)(name="test name")

#     subscription = """
#         subscription SomeModelUpdated($id: ID){
#             someModelUpdated(id: $id) {
#                 name
#             }
#         }
#     """

#     await query(subscription, communicator, { "id": s.pk })

#     await database_sync_to_async(s.save)()

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"someModelUpdated": {"name": s.name}},
#         "errors": None,
#     }

#     await communicator.disconnect()

#     post_save.disconnect(
#         post_save_subscription, sender=SomeModel, dispatch_uid="some_model_post_delete"
#     )


# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_custom_event_subscription_succeeds():
#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     subscription = """
#         subscription {
#             customSubscription
#         }
#     """

#     await query(subscription, communicator)

#     await asyncio.sleep(0.5) # need to get rid of these

#     event = SubscriptionEvent(operation=CUSTOM_EVENT, instance="some value")

#     await sync_to_async(event.send)()

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"customSubscription": "some value"},
#         "errors": None,
#     }

#     await communicator.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.django_db
# async def test_model_subscription_with_custom_group():
#     def custom_post_save_subscription(sender, instance, created, **kwargs):
#         if not created:
#             ModelSubscriptionEvent(
#                 operation=UPDATED,
#                 instance=instance,
#                 group=f"modelUpdated.{instance.id}"
#             ).send()

#     post_save.connect(
#         custom_post_save_subscription, sender=SomeModel, dispatch_uid="some_model_updated"
#     )

#     communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
#     connected, subprotocol = await communicator.connect()
#     assert connected

#     s = await database_sync_to_async(SomeModel.objects.create)(name="test name")

#     subscription = """
#         subscription SomeModelUpdated($id: ID){
#             someModelUpdatedCustom(id: $id) {
#                 name
#             }
#         }
#     """

#     await query(subscription, communicator, { "id": s.pk })

#     await asyncio.sleep(0.5) # need to get rid of these

#     await database_sync_to_async(s.save)()

#     response = await communicator.receive_json_from()

#     assert response["payload"] == {
#         "data": {"someModelUpdatedCustom": {"name": s.name}},
#         "errors": None,
#     }

#     await communicator.disconnect()

#     post_save.disconnect(
#         custom_post_save_subscription, sender=SomeModel, dispatch_uid="some_model_updated"
#     )