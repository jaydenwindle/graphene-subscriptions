SECRET_KEY = 1

INSTALLED_APPS = ["graphene_subscriptions", "tests"]

GRAPHENE = {"SCHEMA": "tests.schema.schema"}

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "tests/django.sqlite"}
}

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
