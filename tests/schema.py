import graphene
from graphene_django.types import DjangoObjectType
from rx import Observable

from tests.models import SomeModel


CUSTOM_EVENT = "custom_event"


class SomeModelType(DjangoObjectType):
    class Meta:
        model = SomeModel


class SomeModelCreatedSubscription(graphene.ObjectType):
    some_model_created = graphene.Field(SomeModelType)

    def resolve_some_model_created(root, info):
        return root.subscribe('someModelCreated')


class SomeModelUpdatedSubscription(graphene.ObjectType):
    some_model_updated = graphene.Field(SomeModelType, id=graphene.String())

    def resolve_some_model_updated(root, info, id):
        return root.subscribe(f'someModelUpdated.{id}')

class SomeModelDeletedSubscription(graphene.ObjectType):
    some_model_deleted = graphene.Field(SomeModelType, id=graphene.String())

    def resolve_some_model_deleted(root, info, id):
        return root.subscribe(f'someModelDeleted.{id}')


class CustomSubscription(graphene.ObjectType):
    custom_subscription = graphene.String()

    def resolve_custom_subscription(root, info):
        return root.subscribe('customSubscription')


class Subscription(
    CustomSubscription,
    SomeModelCreatedSubscription,
    SomeModelUpdatedSubscription,
    SomeModelDeletedSubscription
):
    hello = graphene.String()

    def resolve_hello(root, info):
        return Observable.of("hello world!")


class Query(graphene.ObjectType):
    base = graphene.String()


schema = graphene.Schema(query=Query, subscription=Subscription)
