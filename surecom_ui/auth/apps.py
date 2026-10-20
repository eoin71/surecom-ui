from django.apps import AppConfig


class SurecomAuthConfig(AppConfig):
    name = "surecom_ui.auth"
    # "auth" alone would clash with django.contrib.auth
    label = "surecom_auth"
    verbose_name = "Surecom sign-in"

    def ready(self):
        from . import checks  # noqa: F401  registers the system checks
