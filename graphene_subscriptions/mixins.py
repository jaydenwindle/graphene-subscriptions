from django_lifecycle import LifecycleModelMixin, hook

from graphene_subscriptions.events import trigger_subscription


class SubscriptionModelMixin(LifecycleModelMixin):

    @hook('after_create')
    def trigger_subscription_on_create(self):
        model_name = self.__class__.__name__
        model_camel_case = model_name[0].lower() + model_name[1:]

        trigger_subscription(f"{model_camel_case}Created", self)
        

    @hook('after_update')
    def trigger_subscription_on_update(self):
        model_name = self.__class__.__name__
        model_camel_case = model_name[0].lower() + model_name[1:]

        trigger_subscription(f"{model_camel_case}Updated.{self.pk}", self)

    @hook('before_delete')
    def trigger_subscription_on_delete(self):
        model_name = self.__class__.__name__
        model_camel_case = model_name[0].lower() + model_name[1:]

        trigger_subscription(f"{model_camel_case}Deleted.{self.pk}", self)
        pass