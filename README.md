# Graphene Subscriptions

<p>
    <a href="" alt="License">
        <img src="https://img.shields.io/pypi/l/graphene-subscriptions" /></a>
    <a href="https://pypi.org/project/graphene-subscriptions/" alt="Pypi">
        <img src="https://img.shields.io/pypi/v/graphene-subscriptions" /></a>
    <a href="https://github.com/jaydenwindle/graphene-subscriptions/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/jaydenwindle/graphene-subscriptions" /></a>
    <a href="https://github.com/jaydenwindle/graphene-subscriptions/actions?query=workflow%3ATests">
        <img src="https://github.com/jaydenwindle/graphene-subscriptions/workflows/Tests/badge.svg" alt="build status"></a>
    <a href="https://twitter.com/intent/follow?screen_name=jayden_windle">
        <img src="https://img.shields.io/twitter/follow/jayden_windle?style=social&logo=twitter"
            alt="follow on Twitter"></a>
</p>

A plug-and-play GraphQL subscription implementation for Graphene + Django built using Django Channels. Provides support for model creation, mutation and deletion subscriptions out of the box.


## Installation

1. Install `graphene-subscriptions`
    ```bash
    $ pip install graphene-subscriptions
    ```

2. Add `graphene_subscriptions` to `INSTALLED_APPS`:

    ```python
    # your_project/settings.py
    INSTALLED_APPS = [
        # ...
        'graphene_subscriptions'
    ]
    ```

3. Add Django Channels to your project (see: [Django Channels installation docs](https://channels.readthedocs.io/en/latest/installation.html)) and set up [Channel Layers](https://channels.readthedocs.io/en/latest/topics/channel_layers.html). If you don't want to set up a Redis instance in your dev environment yet, you can use the in-memory Channel Layer:

    ```python
    # your_project/settings.py
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }
    ```

4. Add `GraphqlSubscriptionConsumer` to your `routing.py` file.

    ```python
    # your_project/routing.py
    from channels.routing import ProtocolTypeRouter, URLRouter
    from django.urls import path 

    from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer

    application = ProtocolTypeRouter({
        "websocket": URLRouter([
            path('graphql/', GraphqlSubscriptionConsumer)
        ]),
    })
    ```

5. Add `SubscriptionModelMixin` to any models you want to enable subscriptions for

    ```python
    # your_app/models.py
    from graphene_subscriptions.models import SubscriptionModelMixin

    class YourModel(SubscriptionModelMixin, models.Model):
        # ...
    ```

6. Define your subscriptions and connect them to your project schema

    ```python
    #your_project/schema.py
    import graphene
    from graphene_django.types import DjangoObjectType

    from your_app.models import YourModel


    class YourModelType(DjangoObjectType):
        class Meta:
            model = YourModel


    class YourModelCreatedSubscription(graphene.ObjectType):
        your_model_created = graphene.Field(YourModelType)

        def resolve_your_model_created(root, info):
            return root.subscribe('yourModelCreated')


    class Query(graphene.ObjectType):
        base = graphene.String()


    class Subscription(YourModelCreatedSubscription):
        pass


    schema = graphene.Schema(
        query=Query,
        subscription=Subscription
    )
    ```


## Defining Subscriptions

Subscriptions in Graphene are defined as normal `ObjectType`'s. Each subscription field resolver must return an observable which emits values matching the field's type.

A simple hello world subscription (which returns the value `"hello world!"` every 3 seconds) could be defined as follows:

```python
import graphene
from rx import Observable

class Subscription(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return Observable.interval(3000) \
                         .map(lambda i: "hello world!")
```

## Subscribing to Events

Most of the time you will want your subscriptions to be able to listen for events that occur in other parts of your application. When you define a subscription resolver, you can use the `subscribe` method of the `root` value to subscribe to a set of events. `subscribe` takes a unique group name as an argument, and returns an `Observable` of all events that are sent to that group. Since the return value of `root.subscribe` is an `Observable`, you can apply any `rxpy` operations and return the result.

```python
class CustomSubscription(graphene.ObjectType):
    custom_subscription = graphene.String()

    def resolve_custom_subscription(root, info):
        return root.subscribe('customSubscription')
```

You can then trigger events from other parts of your application using the `trigger_subscription` helper. `trigger_subscription` takes two arguments: the name of the group to send the event to, and the value to send. Make sure that the value you pass to `trigger_subscription` is compatible with the return type you've defined for your subscription resolver, and is either a Django model or a JSON serializable value.

```python
from graphene_subscriptions.events import trigger_subscription

trigger_subscription('trigger_subscription', 'hello world!')
```


## Model Events

Often you'll want to define subscriptions that fire when a Django model is created, updated, or deleted. `graphene-subscriptions` includes a handy model mixin that configures the triggering of these events for you. You can use it by configuring your model to inherit from `SubscriptionModelMixin`.

```python
# your_app/models.py
from graphene_subscriptions.models import SubscriptionModelMixin

class YourModel(SubscriptionModelMixin, models.Model):
    # ...
```

`SubscriptionModelMixin` will create unique group names for created, updated, and deleted events based on the name of your model, and will send events to these groups automatically.


## Model Created Subscriptions

`SubscriptionModelMixin` automatically sends model created events to a unique group called `"<yourModelName>Created"`. For example, if your model is called `YourModel`, then model created events will be sent to the group `"yourModelCreated"`.

You can create a model created subscription that listens for events in this group and returns them to the client by using the `root.subscribe` helper, like so:

```python
class YourModelCreatedSubscription(graphene.ObjectType):
    your_model_created = graphene.Field(YourModelType)

    def resolve_your_model_created(root, info):
        return root.subscribe('yourModelCreated')
```


### Model Updated Subscriptions

Much like model created events, `SubscriptionModelMixin` automatically sends model updated events to a group called `"<yourModelName>Updated.<your_model_id>"`. For example, if your model is called `YourModel` and an instance with `pk == 1` is updated, then a model updated event will be sent to the group `"yourModelUpdated.1"`.

Your subscription resolver can send model updated events from this group to the client by using the `root.subscribe` helper:

```python
class YourModelUpdatedSubscription(graphene.ObjectType):
    your_model_updated = graphene.Field(YourModelType, id=graphene.String())

    def resolve_your_model_updated(root, info, id):
        return root.subscribe(f'yourModelUpdated.{id}')
```


### Model Deleted Subscriptions

In a similar manner, `SubscriptionModelMixin` automatically sends model deleted events to a group called `"<yourModelName>Deleted.<your_model_id>"`. For example, if your model is called `YourModel` and an instance with `pk == 1` is deleted, then a model deleted event will be sent to the group `"yourModelDeleted.1"`.

Your subscription resolver can send model deleted events from this group to the client by using the `root.subscribe` helper:

```python
class YourModelDeletedSubscription(graphene.ObjectType):
    your_model_deleted = graphene.Field(YourModelType, id=graphene.String())

    def resolve_your_model_deleted(root, info, id):
        return root.subscribe(f'yourModelDeleted.{id}')
```


## Contributing

PRs and other contributions are very welcome! To set up `graphene_subscriptions` in a development envrionment, do the following:

1. Clone the repo
    ```bash
    $ git clone git@github.com:jaydenwindle/graphene-subscriptions.git
    ```

2. Install [poetry](https://poetry.eustace.io/)
    ```bash
    $ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
    ```
3. Install dependencies
    ```bash
    $ poetry install
    ```

4. Run the test suite
    ```bash
    $ poetry run pytest
    ```