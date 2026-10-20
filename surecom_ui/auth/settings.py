"""
Settings shared by every app that signs in with Microsoft 365.

In the app's settings.py, after DEBUG is set:

    from surecom_ui.auth.settings import entra_settings
    globals().update(entra_settings(debug=DEBUG))

Reads these environment variables:

    MICROSOFT_TENANT_ID      Directory (tenant) ID of the company tenant
    MICROSOFT_CLIENT_ID      Application (client) ID of the app registration
    MICROSOFT_CLIENT_SECRET  Client secret value
    ALLOWED_EMAIL_DOMAINS    Comma-separated, e.g. "surecom.ie"
"""

import os

# Used when MICROSOFT_TENANT_ID is unset. allauth's default tenant is "common",
# which accepts any Microsoft account in the world; an invalid tenant makes
# Microsoft refuse the sign-in instead. The system check also warns.
MISSING_TENANT = "missing-tenant-id"


def parse_domains(value):
    """'Surecom.ie, @example.com' -> ['surecom.ie', 'example.com']"""
    return [d.strip().lstrip("@").lower() for d in (value or "").split(",") if d.strip()]


def entra_settings(*, debug=False, environ=None):
    """Return the settings block for Microsoft-only sign-in with a superuser fallback"""
    env = os.environ if environ is None else environ

    settings = {
        "SOCIALACCOUNT_PROVIDERS": {
            "microsoft": {
                "APPS": [
                    {
                        "client_id": env.get("MICROSOFT_CLIENT_ID", ""),
                        "secret": env.get("MICROSOFT_CLIENT_SECRET", ""),
                        "settings": {"tenant": env.get("MICROSOFT_TENANT_ID") or MISSING_TENANT},
                    }
                ],
            }
        },
        # Microsoft only: removes password login, signup and password reset
        "SOCIALACCOUNT_ONLY": True,
        "ACCOUNT_EMAIL_VERIFICATION": "none",  # required by SOCIALACCOUNT_ONLY
        "SOCIALACCOUNT_AUTO_SIGNUP": True,
        "SOCIALACCOUNT_LOGIN_ON_GET": False,  # the sign-in button POSTs, with CSRF
        "SOCIALACCOUNT_ADAPTER": "surecom_ui.auth.adapters.TenantSocialAccountAdapter",
        "SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS": parse_domains(env.get("ALLOWED_EMAIL_DOMAINS")),
        # The only backend: passwords for superusers, sessions for everyone
        "AUTHENTICATION_BACKENDS": ["surecom_ui.auth.backends.SuperuserPasswordBackend"],
        "LOGIN_URL": "account_login",
    }
    if not debug:
        # Callback URLs must be https behind the proxy
        settings["ACCOUNT_DEFAULT_HTTP_PROTOCOL"] = "https"
    return settings
