from django.db import models
from django.db.models.signals import post_save, post_delete
from graphene import ObjectType, Field
from graphene.types.objecttype import ObjectTypeOptions
from graphene.types import Interface
from graphene.types.utils import yank_fields_from_attrs
from .events import ModelSubscriptionEvent, CREATED, UPDATED, DELETED
from graphene.utils.props import props

class SubscriptionOptions(ObjectTypeOptions):
    model = None
    name = None
    description = None
    arguments = None
    output = None
    resolver = None
    interfaces = ()

class DjangoObjectSubscription(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        model=None,
        name=None,
        description=None,
        interfaces=(),
        resolver=None,
        output=None,
        _meta=None,
        arguments=None,
        **options
    ):

        assert model, "All Objects must define a Meta class with the model in it"
        assert issubclass(model, models.Model), "Model value must be a valid Django model"

        assert output, "Output Type must be defined in the Meta class"
        assert issubclass(output, ObjectType), "Outout Type must be a valid graphene object type"
        
        if not _meta:
            _meta = SubscriptionOptions(cls)

        output = output or getattr(cls, "Output", None)
        fields = {}

        for interface in interfaces:
            assert issubclass(
                interface, Interface
            ), f'All interfaces of {cls.__name__} must be a subclass of Interface. Received "{interface}".'
            fields.update(interface._meta.fields)

        if not arguments:
            input_class = getattr(cls, "Arguments", None)
            if input_class:
                arguments = props(input_class)
            else:
                arguments = {}

        if not resolver:
            resolver = cls._resolver

        assert hasattr(cls, "subscribe"), "All subscribtions must define a subscribe method in it"

        post_save.connect(DjangoObjectSubscription.post_save_subscription, sender=model)
        post_delete.connect(DjangoObjectSubscription.post_delete_subscription, sender=model)

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

        _meta.interfaces = interfaces
        _meta.output = output
        _meta.resolver = resolver
        _meta.arguments = arguments
        _meta.name = name
        _meta.model = model
        _meta.description = description

        super(DjangoObjectSubscription, cls).__init_subclass_with_meta__(_meta=_meta, name=name, description=description, **options)
        

    @staticmethod
    def post_save_subscription(sender, instance, created, *args, **kwargs):
        event = ModelSubscriptionEvent(
            operation=CREATED if created else UPDATED, instance=instance
        )
        event.send()

    @staticmethod
    def post_delete_subscription(sender, instance, *args, **kwargs):
        event = ModelSubscriptionEvent(operation=DELETED, instance=instance)
        event.send()

    @classmethod
    def resolve(cls, root, info, event, *args, **kwargs):
        try:
            return cls.subscribe(root, info, event.operation, event.instance, *args, **kwargs)
        except AttributeError:
            return cls.subscribe(root, info, *args, **kwargs)

    @classmethod
    def _resolver(cls, root, info, *args, **kwargs):
        return root.map(lambda event: cls.resolve(root, info, event, *args, **kwargs))

    @classmethod
    def Field(cls, name=None, description=None, deprecation_reason=None, required=False):
        return Field(
            cls._meta.output, 
            args=cls._meta.arguments,
            resolver=cls._meta.resolver,
            name=name,
            description=description or cls._meta.description,
            deprecation_reason=deprecation_reason,
            required=required,
        )
