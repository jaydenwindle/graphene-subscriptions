from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    name = 'subscriptions'

    def ready(self):
        import subscriptions.signals
