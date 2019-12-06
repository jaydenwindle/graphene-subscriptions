import importlib
from django.db import models
from django.core.serializers import serialize, deserialize

CREATED = "created"
UPDATED = "updated"
DELETED = "deleted"


class SubscriptionEvent:
    def __init__(self, operation=None, instance=None):
        self.operation = operation
        self.instance = instance

    def to_dict(self):
        return {
            "operation": self.operation,
            "instance": self.instance,
            "__class__": (self.__module__, self.__class__.__name__),
        }

    @staticmethod
    def from_dict(_dict):
        module_name, class_name = _dict.get("__class__")
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)

        return cls(operation=_dict.get("operation"), instance=_dict.get("instance"))


class ModelSubscriptionEvent(SubscriptionEvent):
    def __init__(self, operation=None, instance=None):
        super(ModelSubscriptionEvent, self).__init__(operation, instance)

        if type(self.instance) == str:
            # deserialize django object
            self.instance = list(deserialize("json", self.instance))[0].object

        if not isinstance(self.instance, models.Model):
            raise ValueError(
                "ModelSubscriptionEvent instance value must be a Django model"
            )

    def to_dict(self):
        _dict = super(ModelSubscriptionEvent, self).to_dict()

        _dict["instance"] = serialize("json", [self.instance])

        return _dict
