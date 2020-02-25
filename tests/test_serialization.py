import pytest

from graphene_subscriptions.events import serialize_value, deserialize_value
from tests.models import SomeModel

def test_serialize_deserialize_model():
    instance = SomeModel(name="test")

    serialized = serialize_value(instance)

    deserialized = deserialize_value(serialized)

    assert isinstance(deserialized, SomeModel)
    assert deserialized.name == "test"

def test_serialize_deserialize_value():
    assert deserialize_value(serialize_value(1)) == 1
    assert deserialize_value(serialize_value("string")) == "string"
    assert deserialize_value(serialize_value(1.1)) == 1.1
    assert deserialize_value(serialize_value([1, 2])) == [1, 2]
    assert deserialize_value(serialize_value({"hello": "world"})) == {"hello": "world"}
    