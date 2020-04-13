import pytest
from channels.testing import WebsocketCommunicator

from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer


@pytest.mark.asyncio
async def test_consumer_connection_init():
    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to({"type": "connection_init"})

    response = await communicator.receive_json_from()

    assert response["type"] == "connection_ack"


@pytest.mark.asyncio
async def test_consumer_connection_terminate():
    communicator = WebsocketCommunicator(GraphqlSubscriptionConsumer, "/graphql/")
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to({"type": "connection_terminate"})

    response = await communicator.receive_output()

    assert response["type"] == "websocket.close"
    assert response["code"] == 1000
