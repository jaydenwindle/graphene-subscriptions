import json
from django.db import models
from django.core.serializers import serialize, deserialize
from django.core.serializers.base import DeserializationError

def serialize_value(value):
    if isinstance(value, models.Model):
        return serialize("json", [value])

    return json.dumps(value) 

def deserialize_value(value):
    try:
        return list(deserialize("json", value))[0].object
    except DeserializationError:
        return json.loads(value)
