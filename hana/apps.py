from django.apps import AppConfig


class HanaConfig(AppConfig):
    name = 'hana'

    def ready(self):
        import hana.signals