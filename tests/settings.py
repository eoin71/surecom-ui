"""
Minimal project for the package tests:

    pip install -e ".[auth]"
    python -m django test tests --settings=tests.settings
"""

from surecom_ui.auth.settings import entra_settings

SECRET_KEY = "tests-only"
DEBUG = True
ALLOWED_HOSTS = ["testserver"]
ROOT_URLCONF = "tests.urls"
STATIC_URL = "/static/"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "surecom_ui",
    "surecom_ui.auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "surecom_ui.context_processors.ui",
        ],
    },
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

globals().update(entra_settings(debug=DEBUG, environ={
    "MICROSOFT_TENANT_ID": "tenant-123",
    "MICROSOFT_CLIENT_ID": "client-abc",
    "MICROSOFT_CLIENT_SECRET": "secret-xyz",
    "ALLOWED_EMAIL_DOMAINS": "surecom.ie",
}))
