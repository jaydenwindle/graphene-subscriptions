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
        return root.subscribe('someModelCreated')


class TestSubscription(graphene.ObjectType):
    test_subscription = graphene.String()

    def resolve_test_subscription(root, info):
        return root.subscribe('testSubscription')


class Subscription(
    TestSubscription
):
    hello = graphene.String()

    def resolve_hello(root, info):
        return Observable.of("hello world!")


class Query(graphene.ObjectType):
    base = graphene.String()


schema = graphene.Schema(query=Query, subscription=Subscription)
