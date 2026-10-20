"""
Test helpers for apps using surecom_ui.auth.

Runs the real allauth sign-in flow (start, Microsoft redirect, callback), with
only Microsoft's token and Graph endpoints mocked:

    from surecom_ui.auth.testing import MicrosoftSignInMixin

    @MicrosoftSignInMixin.configured
    class SignInTests(MicrosoftSignInMixin, TestCase):
        def test_sign_in(self):
            response = self.sign_in("aoife@surecom.ie")
"""

import json
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.test import override_settings

from .adapters import TenantSocialAccountAdapter

LOGIN_URL = "/accounts/microsoft/login/"
CALLBACK_URL = "/accounts/microsoft/login/callback/"

TEST_TENANT = "tenant-123"
TEST_SETTINGS = {
    "SOCIALACCOUNT_PROVIDERS": {
        "microsoft": {
            "APPS": [{"client_id": "client-abc", "secret": "secret-xyz", "settings": {"tenant": TEST_TENANT}}],
        }
    },
    "SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS": ["surecom.ie"],
}


class FakeResponse:
    """Just enough of requests.Response for allauth's OAuth2 client and the Graph call"""

    def __init__(self, data, status_code=200):
        self.status_code = status_code
        self.text = json.dumps(data)
        self.content = self.text.encode()
        self.headers = {"content-type": "application/json"}
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def graph_profile(email, **overrides):
    """A Microsoft Graph /me response for the given address"""
    profile = {
        "id": f"id-{email}",
        "mail": email,
        "userPrincipalName": email,
        "givenName": "Aoife",
        "surname": "Byrne",
        "displayName": "Aoife Byrne",
        "mailNickname": email.split("@")[0],
    }
    profile.update(overrides)
    return profile


class MicrosoftSignInMixin:
    """Signs in through Microsoft with the HTTP calls mocked. Use with a Django TestCase."""

    # Class decorator: test tenant and client, and "surecom.ie" as the allowed domain
    configured = override_settings(**TEST_SETTINGS)

    def sign_in(self, profile, next_url=None):
        """Complete a sign-in. ``profile`` is an email or a full graph_profile() dict."""
        if isinstance(profile, str):
            profile = graph_profile(profile)

        start = self.client.post(LOGIN_URL + (f"?next={next_url}" if next_url else ""))
        self.assertEqual(start.status_code, 302)
        self.authorize_url = start["Location"]
        state = parse_qs(urlparse(self.authorize_url).query)["state"][0]

        session = mock.MagicMock()
        session.__enter__.return_value = session  # newer allauth uses `with session:`
        session.request.return_value = FakeResponse({"access_token": "token", "token_type": "Bearer"})
        session.get.return_value = FakeResponse(profile)
        with mock.patch.object(TenantSocialAccountAdapter, "get_requests_session", return_value=session):
            return self.client.get(CALLBACK_URL, {"code": "code", "state": state})

    def signed_in_user(self, url="/"):
        """The user on the next request (anonymous if the sign-in didn't stick)"""
        return self.client.get(url).wsgi_request.user
