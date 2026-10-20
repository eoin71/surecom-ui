"""
Deploy-time checks for Microsoft sign-in.

Warnings rather than errors, so a missing secret doesn't stop `migrate` or the
test runner. Sign-in fails closed either way: an unset tenant is refused by
Microsoft, and an empty domain allowlist rejects every account.
"""

from django.conf import settings
from django.core.checks import Tags, Warning, register

from .settings import MISSING_TENANT


def _microsoft_app():
    providers = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
    apps = providers.get("microsoft", {}).get("APPS") or [{}]
    return apps[0]


@register(Tags.security)
def check_microsoft_settings(app_configs, **kwargs):
    issues = []
    app = _microsoft_app()

    missing = []
    if app.get("settings", {}).get("tenant") in (None, "", MISSING_TENANT):
        missing.append("MICROSOFT_TENANT_ID")
    if not app.get("client_id"):
        missing.append("MICROSOFT_CLIENT_ID")
    if not app.get("secret"):
        missing.append("MICROSOFT_CLIENT_SECRET")
    if missing:
        issues.append(Warning(
            f"Microsoft sign-in is not configured: {', '.join(missing)} not set.",
            hint="Set the environment variables, or no one can sign in except the break-glass superuser.",
            id="surecom_auth.W001",
        ))

    if not getattr(settings, "SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS", []):
        issues.append(Warning(
            "ALLOWED_EMAIL_DOMAINS is empty, so every Microsoft sign-in will be rejected.",
            hint='Set ALLOWED_EMAIL_DOMAINS, e.g. "surecom.ie".',
            id="surecom_auth.W002",
        ))
    return issues


@register()
def check_app_order(app_configs, **kwargs):
    installed = list(settings.INSTALLED_APPS)
    issues = []

    if "allauth.socialaccount.providers.microsoft" not in installed:
        issues.append(Warning(
            "allauth.socialaccount.providers.microsoft is not in INSTALLED_APPS.",
            id="surecom_auth.W003",
        ))

    def position(name):
        return next((i for i, app in enumerate(installed) if app.split(".apps.")[0] == name), None)

    ours, allauth = position("surecom_ui.auth"), position("allauth")
    if ours is not None and allauth is not None and ours > allauth:
        issues.append(Warning(
            '"surecom_ui.auth" must come before "allauth" in INSTALLED_APPS.',
            hint="Otherwise allauth's own sign-in templates are used instead of the shared ones.",
            id="surecom_auth.W004",
        ))
    return issues
