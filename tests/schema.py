import graphene
from graphene_django.types import DjangoObjectType
from rx import Observable

from graphene_subscriptions.events import CREATED, UPDATED, DELETED

from tests.models import SomeModel


CUSTOM_EVENT = "custom_event"


class SomeModelType(DjangoObjectType):
    class Meta:
        model = SomeModel


class SomeModelCreatedSubscription(graphene.ObjectType):
    some_model_created = graphene.Field(SomeModelType)

    def resolve_some_model_created(root, info):
        return root.filter(
            lambda event: event.operation == CREATED
            and isinstance(event.instance, SomeModel)
        ).map(lambda event: event.instance)


class SomeModelUpdatedSubscription(graphene.ObjectType):
    some_model_updated = graphene.Field(SomeModelType, id=graphene.ID())

    def resolve_some_model_updated(root, info, id):
        return root.filter(
            lambda event: event.operation == UPDATED
            and isinstance(event.instance, SomeModel)
            and event.instance.pk == int(id)
        ).map(lambda event: event.instance)


class SomeModelUpdatedCustomSubscription(graphene.ObjectType):
    some_model_updated_custom = graphene.Field(SomeModelType, id=graphene.ID())

    def resolve_some_model_updated_custom(root, info, id):
        info.context.subscribe(f"modelUpdated.{id}")
        return root.map(lambda event: event.instance)


class SomeModelDeletedSubscription(graphene.ObjectType):
    some_model_deleted = graphene.Field(SomeModelType, id=graphene.ID())

    def resolve_some_model_deleted(root, info, id):
        return root.filter(
            lambda event: event.operation == DELETED
            and isinstance(event.instance, SomeModel)
            and event.instance.pk == int(id)
        ).map(lambda event: event.instance)


class CustomEventSubscription(graphene.ObjectType):
    custom_subscription = graphene.String()

    def resolve_custom_subscription(root, info):
        return root.filter(lambda event: event.operation == CUSTOM_EVENT).map(
            lambda event: event.instance
        )


class Subscription(
    CustomEventSubscription,
    SomeModelCreatedSubscription,
    SomeModelUpdatedSubscription,
    SomeModelUpdatedCustomSubscription,
    SomeModelDeletedSubscription,
):
    hello = graphene.String()

    def resolve_hello(root, info):
        return Observable.of("hello world!")


class Query(graphene.ObjectType):
    base = graphene.String()


schema = graphene.Schema(query=Query, subscription=Subscription)
