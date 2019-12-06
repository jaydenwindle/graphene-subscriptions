# Graphene Subscriptions

<p>
    <a href="" alt="License">
        <img src="https://img.shields.io/github/license/jaydenwindle/graphene-subscriptions" /></a>
    <a href="https://github.com/jaydenwindle/graphene-subscriptions/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/jaydenwindle/graphene-subscriptions" /></a>
    <a href="https://github.com/jaydenwindle/graphene-subscriptions/actions?query=workflow%3A%22Test+Package%22">
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
        ...
        'graphene_subscriptions'
    ]
    ```

3. Add Django Channels to your project (see: [Django Channels installation docs](https://channels.readthedocs.io/en/latest/installation.html))

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

5. Connect signals for any models you want to create subscriptions for

    ```python
    # your_app/signals.py
    from django.db.models.signals import post_save, post_delete
    from graphene_subscriptions.signals import post_save_subscription, post_delete_subscription

    from your_app.models import YourModel

    post_save.connect(post_save_subscription, sender=YourModel, dispatch_uid="your_model_post_save")
    post_delete.connect(post_delete_subscription, sender=YourModel, dispatch_uid="your_model_post_delete")

    # your_app/apps.py
    from django.apps import AppConfig

    class YourAppConfig(AppConfig):
        name = 'your_app'

        def ready(self):
            import your_app.signals
    ```

6. Define your subscriptions and connect them to your project schema

    ```python
    #your_project/schema.py
    import graphene

    from your_app.graphql.subscriptions import YourSubscription


    class Query(graphene.ObjectType):
        base = graphene.String()


    class Mutation(graphene.ObjectType):
        pass


    class Subscription(YourSubscription):
        pass


    schema = graphene.Schema(
        query=Query,
        mutation=Mutation,
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
                         .map(lambda: "hello world!")
```

## Receiving Model Events

Each subscription that you define will receive a an `Observable` of `SubscriptionEvent`'s as the `root` parameter, which will emit a new `SubscriptionEvent` each time one of the connected signals are fired.

A `SubscriptionEvent` has two attributes: the `operation` that triggered the event, usually `CREATED`, `UPDATED` or `DELETED`) and the `instance` that triggered the signal.

Since `root` is an `Observable`, you can apply any `rxpy` operations before returning it.

### Model Created Subscriptions

For example, let's create a subscription called `yourModelCreated` that will be fired whenever an instance of `YourModel` is created. Since `root` receives a new event *every time a connected signal is fired*, we'll need to filter for only the events we want. In this case, we want all events where `operation` is `created` and the event `instance` is an instance of our model.

```python
import graphene
from graphene_django.types import DjangoObjectType
from graphene_subscriptions.events import CREATED

from your_app.models import YourModel


class YourModelType(DjangoObjectType)
    class Meta:
        model = YourModel


class Subscription(graphene.ObjectType):
    your_model_created = graphene.Field(YourModelType)

    def resolve_your_model_created(root, info):
        return root.filter(
            lambda event:
                event.operation == CREATED and
                isinstance(event.instance, YourModel)
        ).map(lambda event: event.instance)
```

### Model Updated Subscriptions

You can also filter events based on a subscription's arguments. For example, here's a subscription that fires whenever a model is updated:

```python
import graphene
from graphene_django.types import DjangoObjectType
from graphene_subscriptions.events import UPDATED 

from your_app.models import YourModel


class YourModelType(DjangoObjectType)
    class Meta:
        model = YourModel


class Subscription(graphene.ObjectType):
    your_model_updated = graphene.Field(YourModelType, id=graphene.ID())

    def resolve_your_model_updated(root, info, id):
        return root.filter(
            lambda event:
                event.operation == UPDATED and
                isinstance(event.instance, YourModel) and
                event.instance.pk == int(id)
        ).map(lambda event: event.instance)
```

### Model Updated Subscriptions

Defining a subscription that is fired whenever a given model instance is deleted can be accomplished like so

```python
import graphene
from graphene_django.types import DjangoObjectType
from graphene_subscriptions.events import DELETED 

from your_app.models import YourModel


class YourModelType(DjangoObjectType)
    class Meta:
        model = YourModel


class Subscription(graphene.ObjectType):
    your_model_deleted = graphene.Field(YourModelType, id=graphene.ID())

    def resolve_your_model_deleted(root, info, id):
        return root.filter(
            lambda event:
                event.operation == DELETED and
                isinstance(event.instance, YourModel) and
                event.instance.pk == int(id)
        ).map(lambda event: event.instance)
```


## Production Readiness

This implementation was spun out of an internal implementation I developed which we've been using in production for the past 6 months at [Jetpack](https://www.tryjetpack.com/). We've had relatively few issues with it, and I am confident that it can be reliably used in production environments.

However, being a startup, our definition of production-readiness may be slightly different from your own. Also keep in mind that the scale at which we operate hasn't been taxing enough to illuminate where the scaling bottlenecks in this implementation may hide.

If you end up running this in production, please [reach out](https://twitter.com/jayden_windle) and let me know!


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